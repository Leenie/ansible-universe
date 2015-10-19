# copyright (c) 2015 fclaerhout.fr, released under the MIT license.
# coding: utf-8

"""
Ansible role build tool.

Usage:
  ansible-universe [options] TARGETS...
  ansible-universe --help

Options:
  -W FLAGS, --warnings FLAGS  comma-separated list of flags to enable [default: all]
  -C PATH, --directory PATH   set working directory [default: .]
  -r URL, --repository URL    set HTTP repository
  -v, --verbose               output executed commands
  -h, --help                  display full help text
  -x GLOBS, --exclude GLOBS   file patterns to exclude [default: .*]
  --no-color                  disable colored output

TARGET:
  * show     show role metadata
  * init     instantiate role template
  * dist     generate ansible distributable role files
  * clean    delete non-distributable role files
  * check    include role in a dummy playbook and check syntax
  * package  package role
  * publish  publish role to a web repository

Lifecycles:
  * show
  * init
  * clean
  * publish < package < check < dist

Example:
  $ mkdir foo
  $ ansible-universe -C foo init check

Universe uses the ansible-galaxy manifest (meta/main.yml) with extra attributes:
  * prefix        variable prefix, defaults to rolename
  * version       role version
  * variables     maps names to descriptions
  * include_when  maps tasks filename to include conditions
"""

import textwrap, fnmatch, glob, sys, os

import docopt, jinja2, fckit, yaml # 3rd-party

MANIFESTS = tuple(dict({"name": name}, **__import__(name, globals()).MANIFEST) for name in (
	"copy_has_owner",
	"manifest_has_author",
	"manifest_has_license",
	"manifest_has_platforms",
	"manifest_has_version",
	"subdir_is_defined")) #FIXME

class Error(fckit.Error): pass

def unmarshall(path, default = None):
	"custom unmarshaller with yaml support"
	def _unmarshall_yaml(path):
		with open(path, "r") as fp:
			return yaml.load(fp)
	return fckit.unmarshall(
		path = path,
		default = default,
		helpers = {".yml": _unmarshall_yaml})

def marshall(obj, path, extname = None):
	"custom marshaller with yaml support"
	def _marshall_yaml(obj, fp):
		yaml.dump(obj, fp, explicit_start = True, default_flow_style = False)
	fckit.marshall(
		obj = obj,
		path = path,
		extname = extname,
		helpers = {".yml": _marshall_yaml},
		overwrite = True)

class Role(object):
	"helper object to parse role properties"

	def __init__(self, path = None):
		self.path = path
		self.name = os.path.basename(os.path.abspath(self.path))
		self.defaults_path = os.path.join(self.path, "defaults", "main.yml")
		self.readme_path = os.path.join(self.path, "README.md")
		self.meta_path = os.path.join(self.path, "meta", "main.yml")
		self.vars_path = os.path.join(self.path, "vars", "main.yml")
		self.tasks_path = os.path.join(self.path, "tasks", "main.yml")

	@property
	def manifest(self):
		"return role manifest as a dict"
		if not os.path.exists(self.meta_path):
			raise Error("missing role manifest")
		return unmarshall(self.meta_path) or {}

	@property
	def version(self):
		try:
			return self.manifest["version"]
		except KeyError:
			raise Error("missing 'version' attribute in manifest")

	@property
	def galaxy_info(self):
		try:
			return self.manifest["galaxy_info"]
		except KeyError:
			raise Error("missing 'galaxy_info' attribute in manifest")

	@property
	def author(self):
		try:
			return self.galaxy_info["author"]
		except KeyError:
			raise Error("missing 'author' attribute in manifest")

	@property
	def prefix(self):
		"return prefix for variables, defaults on role name"
		return self.manifest.get("prefix", "%s_" % self.name.lower().replace("-", "_"))

	@property
	def platforms(self):
		"return the list of supported platforms {'name':…, 'versions':…}"
		try:
			return self.galaxy_info["platforms"]
		except:
			raise Error("missing platforms attribute in manifest")

	@property
	def variables(self):
		"return dict mapping variable names to {'constant', 'default', 'description'}"
		res = {}
		for key, value in (unmarshall(self.defaults_path) or {}).items():
			res[key] = {
				"description": None,
				"constant": False,
				"value": value,
			}
		for key, value in (unmarshall(self.vars_path) or {}).items():
			if key in res:
				raise Error(key, "variable both set in vars/ and defaults/")
			else:
				res[key] = {
					"description": None,
					"constant": True,
					"value": value,
				}
		for key, value in self.manifest.get("variables", {}).items():
			if key in res:
				res[key]["description"] = value
			else:
				res[key] = {
					"description": value,
					"constant": False,
					"value": None,
				}
		return res

	@property
	def description(self):
		try:
			return self.galaxy_info["description"]
		except KeyError:
			raise Error("missing 'description' attribute in manifest")

	@property
	def dependencies(self):
		"return list of role dependencies"
		return self.manifest.get("dependencies", ())

	@property
	def include_when(self):
		"return dict mapping tasks/ playbooks to include conditions"
		return self.manifest.get("include_when", {})

#################
# build targets #
#################

def show(role):
	print yaml.dump(
		data = {
			"name": role.name,
			"author": role.author,
			"version": role.version,
			"platforms": role.platforms,
			"variables": role.variables,
			"description": role.description,
		},
		explicit_start = True,
		default_flow_style = False)

def init_manifest(path):
	print "generating", path
	marshall(
		path = path,
		obj = {
			"dependencies": [],
			"inconditions": {},
			"galaxy_info": {
				"min_ansible_version": "1.8.4",
				"description": None,
				"platforms": [],
				"license": "MIT",
				"author": None,
			},
			"variables": {},
			"version": "0.0.1",
		}
	)

def generate_readme(role):
	print "generating %s" % role.readme_path
	template = """
		<!-- THIS IS A GENERATED FILE, DO NOT EDIT -->

		{{ description or "(No description yet.)" }}


		## Supported Platforms

		{% for ptf in platforms %}  * {{ ptf.name }}
		{% else %}
		No supported platform specified (yet.)
		{% endfor %}

		## Variables

		| Name | Value | Constant? | Description |
		|------|-------|-----------|-------------|
		{% for key in variables.keys()|sort %}| {{ key }} | {{ variables[key].value }} | {{ variables[key].constant }} | {{ variables[key].description }} |
		{% endfor %}

		## Usage

		Read the Ansible documentation at https://docs.ansible.com/playbooks_roles.html.


		## Maintenance

		Install [ansible-universe](https://github.com/fclaerho/ansible-universe)
		and run `ansible-universe dist check` to re-generate this distribution.

		The following files are generated or updated based on the role manifest `meta/main.yml`:
		  * tasks/main.yml
		  * README.md

	""".decode("utf-8")
	text = jinja2.Template(textwrap.dedent(template)).render(**{
		"description": role.description,
		"platforms": role.platforms,
		"variables": role.variables,
		"name": role.name,
	})
	marshall(
		obj = text.encode("utf-8"),
		path = role.readme_path,
		extname = ".txt")

def generate_maintask(role):
	print "generating %s" % role.tasks_path
	platforms = role.platforms
	tasks = []
	if platforms:
		tasks.append({
			"name": "assert the target platform is supported",
			"fail": {
				"msg": "unsupported platform -- please contact %s for support" % role.author,
			},
			"when": "ansible_distribution not in %s" % list(platform["name"] for platform in platforms),
		})
	for path in glob.glob(os.path.join(os.path.dirname(role.tasks_path), "*.yml")):
		name = os.path.basename(path)
		fckit.trace("including", name)
		if name in role.include_when:
			tasks.append({
				"name": "%s is included" % name,
				"include": name,
				"when": role.include_when[name],
			})
		else:
			tasks.append({
				"include": name,
			})
	marshall(
		obj = tasks,
		path = role.tasks_path)

def clean(role, build_path):
	if os.path.exists(build_path):
		fckit.remove(build_path)
	for root, dirnames, filenames in os.walk(role.path):
		for filename in filenames:
			path = os.path.join(root, filename)
			if fnmatch.fnmatch(filename, ".*.hmap") or path in (role.readme_path, role.tasks_path):
				fckit.remove(path)

def check(path, role, warning_flags):
	manifests = [
		manifest for manifest in MANIFESTS
		if "all" in warning_flags or manifest.get("flag", manifest["name"]) in warning_flags]
	with open(path, "w") as fp:
		def warning(*strings):
			msg = ": ".join(strings).encode("utf-8")
			sys.stderr.write(fckit.magenta("WARNING! %s\n" % msg))
			fp.write("%s\n" % msg)
		def check_role(manifests):
			for manifest in manifests:
				if not manifest["predicate"](role):
					warning(role.name, manifest["message"])
		def check_objects(objects, manifests):
			for key in objects:
				for manifest in manifests:
					if not manifest["predicate"](objects[key], role):
						warning(key, manifest["message"])
		check_role(
			manifests = filter(lambda manifest: manifest["type"] == "role", manifests))
		check_objects(
			objects = {key: key for key in role.variables},
			manifests = filter(lambda manifest: manifest["type"] == "variable", manifests))
		check_objects(
			objects = {
				basename: basename
				for basename in os.listdir(role.path)
				if not basename.startswith(".") and os.path.isdir(os.path.join(role.path, basename))},
			manifests = filter(lambda manifest: manifest["type"] == "subdir", manifests))
		objects = {}
		for root, _, filenames in os.walk(os.path.dirname(role.tasks_path)):
			for filename in filenames:
				_, extname = os.path.splitext(filename)
				if extname == ".yml":
					path = os.path.join(root, filename)
					tasks = unmarshall(path, default = []) or []
					for idx, task in enumerate(tasks):
						name = task.get("name", "#%i" % (idx + 1))
						objects[name] = task
		check_objects(
			objects = objects,
			manifests = filter(lambda manifest: manifest["type"] == "task", manifests))

def package(path, role):
	print "generating", path
	fckit.check_call("tar", "czf", path, "--exclude", os.path.dirname(path), role.path)

def publish(path, url):
	fckit.check_call("curl", "-k", "-T", path, url)

##############
# entrypoint #
##############

def get_dist_sources(role, exclude):
	"build dist dependency sub-graph"
	targets = {}
	# first, create non-buildable targets out of existing files:
	for root, dirnames, filenames in os.walk(role.path):
		excluded = tuple(
			dirname
			for dirname in dirnames
			for pattern in exclude
			if fnmatch.fnmatch(dirname, pattern))
		for dirname in excluded:
			dirnames.remove(dirname)
		if root != role.path:
			fckit.trace("indexing %s" % root)
			targets[root] = fckit.BuildTarget(
				path = root,
				on_build = None, # cannot build source file
				on_digest = lambda path: None) # no digest for directories
		for filename in filenames:
			if not any(fnmatch.fnmatch(filename, pattern) for pattern in exclude):
				path = os.path.join(root, filename)
				fckit.trace("indexing %s" % path)
				targets[path] = fckit.BuildTarget(
					path = path,
					on_build = None) # cannot build source file
	# second, update targets of files to generate:
	def is_in_defaults_path(key):
		return targets[key].path.startswith(os.path.dirname(role.defaults_path))
	def is_in_vars_path(key):
		return targets[key].path.startswith(os.path.dirname(role.vars_path))
	def is_in_tasks_path(key):
		return targets[key].path.startswith(os.path.dirname(role.tasks_path))
	targets[role.readme_path] = fckit.BuildTarget(
		path = role.readme_path,
		sources = [targets[key] for key in targets\
			if is_in_defaults_path(key) or is_in_vars_path(key) or key == role.meta_path],
		on_build = lambda tgtpath, srcpaths: generate_readme(role))
	targets[role.tasks_path] = fckit.BuildTarget(
		path = role.tasks_path,
		sources = [targets[key] for key in targets\
			if (is_in_tasks_path(key) and key != role.tasks_path) or key == role.meta_path],
		on_build = lambda tgtpath, srcpaths: generate_maintask(role))
	return targets.values()

class Targets(object):

	def __init__(self, role, exclude, warning_flags):
		self.warning_flags = warning_flags
		self.build_path = os.path.join(role.path, ".build")
		self.exclude = exclude
		self.cache = {}
		self.role = role

	def __getitem__(self, key):
		if not key in self.cache:
			if key == "show":
				self.cache[key] = fckit.BuildTarget(
					path = key,
					phony = True,
					on_build = lambda srcpaths: show(self.role))
			elif key == "init":
				self.cache[key] = fckit.BuildTarget(
					path = self.role.meta_path,
					on_build = lambda tgtpath, srcpaths: init_manifest(tgtpath))
			elif key == "clean":
				self.cache[key] = fckit.BuildTarget(
					path = key,
					phony = True,
					on_build = lambda srcpaths: clean(
						role = self.role,
						build_path = self.build_path))
			elif key == "dist":
				self.cache[key] = fckit.BuildTarget(
					path = os.path.join(self.build_path, "dist"),
					sources = get_dist_sources(
						role = self.role,
						exclude = self.exclude),
					on_build = True)
			elif key == "check":
				self.cache[key] = fckit.BuildTarget(
					path = os.path.join(self.build_path, "warnings.txt"),
					sources = [self["dist"]],
					on_build = lambda tgtpath, srcpaths: check(
						path = tgtpath,
						role = self.role,
						warning_flags = self.warning_flags))
			elif key == "package":
				self.cache[key] = fckit.BuildTarget(
					path = os.path.join(self.build_path, "%s-%s.tgz" % (self.role.name, self.role.version)),
					sources = [self["check"]],
					on_build = lambda tgtpath, srcpaths: package(tgtpath, self.role))
			elif key == "publish":
				self.cache[key] = fckit.BuildTarget(
					path = "publish",
					phony = True,
					sources = [self["package"]])
			else:
				raise Error(key, "unknown target")
		return self.cache[key]

def main(args = None):
	opts = docopt.docopt(
		doc = __doc__,
		argv = args)
	try:
		if opts["--no-color"]:
			fckit.disable_colors()
		if opts["--verbose"]:
			fckit.enable_tracing()
		role = Role(opts["--directory"])
		targets = Targets(
			role = role,
			exclude = opts["--exclude"].split(","),
			warning_flags = opts["--warnings"].split(","))
		for key in opts["TARGETS"]:
			fckit.trace("at %s" % key)
			targets[key].build()
	except fckit.Error as exc:
		raise SystemExit(fckit.red(exc))
