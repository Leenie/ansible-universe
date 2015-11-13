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
  -r URL, --repository URL    set HTTP repository [default: http://localhost]
  -v, --verbose               output executed commands
  -h, --help                  display full help text
  -x GLOBS, --exclude GLOBS   comma-separated path patterns to exclude [default: .?*]
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
"""

import textwrap, fnmatch, glob, sys, os

import docopt, jinja2, fckit, yaml # 3rd-party

MANIFESTS = tuple(dict({"name": name}, **__import__(name, globals()).MANIFEST) for name in (
	"copy_has_owner",
	"manifest_has_author",
	"manifest_has_license",
	"manifest_has_platforms",
	"manifest_has_version",
	"subdir_is_defined",
	"syntax_is_ok",
	"task_has_name",
	"task_has_no_remote_user",
	"template_has_owner",
	"variable_is_documented",
	"variable_is_prefixed",
))

################################################################################
# helpers                                                                      #
################################################################################

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

	def __init__(self):
		self._name = os.path.basename(os.getcwd())

	@property
	def name(self):
		return self._name

	@property
	def defaults_path(self):
		return os.path.join("defaults", "main.yml")

	@property
	def readme_path(self):
		return "README.md"

	@property
	def tasks_path(self):
		return os.path.join("tasks", "main.yml")

	@property
	def meta_path(self):
		return os.path.join("meta", "main.yml")

	@property
	def vars_path(self):
		return os.path.join("vars", "main.yml")

	def get_manifest(self):
		"return role manifest as a dict"
		if not os.path.exists(self.meta_path):
			raise Error("missing role manifest")
		return unmarshall(self.meta_path) or {}

	@property
	def version(self):
		try:
			return self.get_manifest()["version"]
		except KeyError:
			raise Error("missing 'version' attribute in manifest")

	@property
	def galaxy_info(self):
		try:
			return self.get_manifest()["galaxy_info"]
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
		return self.get_manifest().get("prefix", "%s_" % self.name.lower().replace("-", "_"))

	@property
	def platforms(self):
		"return the list of supported platforms {'name':…, 'versions':…}"
		try:
			return self.galaxy_info.get("platforms", {})
		except:
			raise Error("missing platforms attribute in manifest")

	def get_variables(self):
		"return dict mapping variable names to {'constant', 'default', 'description'}"
		res = {}
		for key, value in (unmarshall(self.defaults_path) or {}).items():
			res[key] = {
				"description": None,
				"value": value,
				"type": "default"
			}
		for key, value in (unmarshall(self.vars_path) or {}).items():
			if key in res:
				raise Error(key, "variable set twice in vars/ and defaults/")
			else:
				res[key] = {
					"description": None,
					"value": value,
					"type": "var"
				}
		for key, value in self.get_manifest().get("variables", {}).items():
			if key in res:
				res[key]["description"] = value
			else:
				res[key] = {
					"description": value,
					"value": None,
					"type": None
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
		return self.get_manifest().get("dependencies", ())

	@property
	def include_when(self):
		"return dict mapping taskfiles to include conditions"
		return self.get_manifest().get("include_when", {})

	@property
	def usage_complement(self):
		return self.get_manifest().get("usage_complement", None)

	@property
	def maintenance_complement(self):
		return self.get_manifest().get("maintenance_complement", None)

	def is_legacy(self):
		"return True if the main task file contains handcrafted tasks not to be touched"
		return os.path.exists(self.tasks_path)\
			and any("fail" not in task and "include" not in task for task in unmarshall(self.tasks_path))

	def get_readme(self):
		with open(self.readme_path, "r") as fp:
			return fp.read()

################################################################################
# build callbacks                                                              #
################################################################################

def show(role):
	print yaml.dump(
		data = {
			"name": role.name,
			"author": role.author,
			"version": role.version,
			"platforms": role.platforms,
			"variables": role.get_variables(),
			"description": role.description,
			"usage_complement": role.usage_complement,
			"maintenance_complement": role.maintenance_complement,
		},
		explicit_start = True,
		default_flow_style = False)

def init_manifest(path):
	print "generating", path
	marshall(
		path = path,
		obj = {
			"galaxy_info": {
				"min_ansible_version": "1.8.4",
				"description": None,
				"platforms": [],
				"license": "MIT",
				"author": None,
			},
			"variables": {},
			"dependencies": [],
			"include_when": {},
			"version": "0.0.1",
			"usage_complement": "Optional. Indicate additional usage instructions.",
			"maintenance_complement": "Optional. Indicate additional maintenance instructions.",
		}
	)

def generate_readme(role):
	print "generating", role.readme_path
	template = """
		<!-- THIS IS A GENERATED FILE, DO NOT EDIT -->

		{{ description or "(No description yet.)" }} Version {{ version }}.


		## Supported Platforms
		{% for ptf in platforms %}
		  * {{ ptf.name }}{% else %}
		No supported platform specified (yet.)
		{% endfor %}

		## Variables
		{% if variables %}
		| Name | Value | Description |
		|------|-------|-------------|
		{% for key in variables.keys()|sort %}| {{ key }} | {{ ("_("+variables[key].type+":)_") if variables[key].type != None else "" }} {{ variables[key].value if variables[key].value != None else "" }} | {{ variables[key].description }} |
		{% endfor %}
		{% else %}
		No variable.
		{% endif %}

		## Usage

		To use this role from a **playbook**, 
		register its ID in the project `requirements.{txt,yml}` file.
		To add this role as another **role dependency**,
		register its ID in the `dependencies` list of the role manifest `meta/main.yml`.
		For further details,
		please refer to the Ansible documentation at https://docs.ansible.com/playbooks_roles.html.

		{{ usage_complement or "" }}


		## Maintenance

		Install [ansible-universe](https://github.com/fclaerho/ansible-universe)
		and run `ansible-universe check` to re-generate this distribution.

		The following files are generated or updated based on various role assets:
		  * tasks/main.yml
		  * README.md

		{{ maintenance_complement or ""}}

	""".decode("utf-8")
	text = jinja2.Template(textwrap.dedent(template)).render(**{
		"maintenance_complement": role.maintenance_complement,
		"usage_complement": role.usage_complement,
		"description": role.description,
		"platforms": role.platforms,
		"variables": role.get_variables(),
		"version": role.version,
		"name": role.name,
	})
	marshall(
		obj = text.encode("utf-8"),
		path = role.readme_path,
		extname = ".txt")

def generate_maintask(role):
	print "generating", role.tasks_path
	platforms = role.platforms
	tasks = []
	if platforms:
		tasks.append({
			"name": "Assert the target platform is supported",
			"fail": {
				"msg": "unsupported platform -- please contact the role maintainer for support",
			},
			"when": "ansible_distribution not in %s" % list(platform["name"] for platform in platforms),
		})
	if role.is_legacy():
		# backward-compatibility mode: update main task file with platform check
		print "handcrafted main task file, falling back to compatibility mode"
		for task in unmarshall(role.tasks_path):
			if platforms and "fail" in task and task["name"] == tasks[0]["name"]:
				continue # skip check
			else:
				tasks.append(task) # copy everything else
	else:
		# new mode: generate main task file
		for path in glob.glob(os.path.join(os.path.dirname(role.tasks_path), "*.yml")):
			if path == role.tasks_path: continue # skip tasks/main.yml if present
			name = os.path.basename(path)
			fckit.trace("including", name)
			tasks.append({
				"name": "Taskfile %s is included" % name,
				"include": name,
				"when": role.include_when.get(name, True),
			})
	marshall(
		obj = tasks,
		path = role.tasks_path)

def clean(role, build_path):
	if os.path.exists(build_path):
		fckit.remove(build_path)
	if role.is_legacy():
		print "skipping handcrafted main task file"
		generated = (role.readme_path,)
	else:
		generated = (role.readme_path, role.tasks_path)
	for root, dirnames, filenames in os.walk("."):
		for filename in filenames:
			path = os.path.normpath(os.path.join(root, filename))
			if fnmatch.fnmatch(filename, ".*.hmap") or path in generated:
				fckit.remove(path)

def get_tasks(role):
	objects = {}
	for root, _, filenames in os.walk(os.path.dirname(role.tasks_path)):
		for filename in filenames:
			_, extname = os.path.splitext(filename)
			if extname == ".yml":
				path = os.path.join(root, filename)
				try:
					tasks = unmarshall(path, default = []) or []
					for idx, task in enumerate(tasks):
						name = "%s[%s]" % (filename, task.get("name", "#%i" % (idx + 1)))
						objects["task '%s'" % name] = task
				except:
					fckit.trace("invalid task file %s, ignored" % path)
	return objects

def check(path, role, warning_flags):
	manifests = [
		manifest for manifest in MANIFESTS
		if "all" in warning_flags or manifest.get("flag", manifest["name"]) in warning_flags]
	helpers = {
		"marshall": marshall,
		"role": role,
	}
	warnings = []
	def check_objects(objects, manifests):
		for key in objects:
			for manifest in manifests:
				if not manifest["predicate"](objects[key], helpers):
					msg = manifest["message"].encode("utf-8")
					warnings.append(
						"** WARNING: %s\n   source: %s\n   flag: %s"
						% (msg, key, manifest.get("flag", manifest["name"])))
	# check role:
	check_objects(
		objects = {"role '%s'" % role.name: role},
		manifests = filter(lambda manifest: manifest["type"] == "role", manifests))
	# check variables:
	check_objects(
		objects = {"variable '%s'" % key: key for key in role.get_variables()},
		manifests = filter(lambda manifest: manifest["type"] == "variable", manifests))
	# check subdirectories:
	check_objects(
		objects = {
			"subdir '%s'" % basename: basename
			for basename in os.listdir(".")
			if not basename.startswith(".") and os.path.isdir(basename)},
		manifests = filter(lambda manifest: manifest["type"] == "subdir", manifests))
	# check tasks:
	check_objects(
		objects = get_tasks(role),
		manifests = filter(lambda manifest: manifest["type"] == "task", manifests))
	with open(path, "w") as fp:
		fp.write("\n".join(warnings))

def get_source_paths(role, exclude):
	paths = []
	for root, dirnames, filenames in os.walk("."):
		excluded = tuple(
			dirname
			for dirname in dirnames
			for pattern in exclude
			if fnmatch.fnmatch(dirname, pattern))
		for dirname in excluded:
			dirnames.remove(dirname)
		for filename in filenames:
			if not any(fnmatch.fnmatch(filename, pattern) for pattern in exclude):
				path = os.path.normpath(os.path.join(root, filename))
				fckit.trace("indexing", path)
				paths.append(path)
	return paths

def package(path, role, exclude):
	print "generating", path
	paths = ["./%s" % srcpath for srcpath in get_source_paths(
		role = role,
		exclude = exclude)]
	argv = ["tar", "-vczf", os.path.abspath(path)] + paths
	fckit.check_call(*argv)

def publish(path, url):
	print "publishing", path, "to", url
	fckit.check_call("curl", "-k", "-T", path, url)

################################################################################
# build targets                                                                #
################################################################################

def get_dist_sources(role, exclude):
	"build dist dependency sub-graph"
	targets = {}
	# first, create non-buildable targets out of existing files:
	for path in get_source_paths(
		role = role,
		exclude = exclude):
		targets[path] = fckit.BuildTarget(
			path = path,
			on_build = None) # cannot build source file
	# second, update targets of files to generate:
	def is_in_defaults_path(key):
		return targets[key].path.startswith(os.path.dirname(role.defaults_path))
	def is_in_tasks_path(key):
		return targets[key].path.startswith(os.path.dirname(role.tasks_path))
	def is_in_vars_path(key):
		return targets[key].path.startswith(os.path.dirname(role.vars_path))
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
	"on-demand target provider, e.g. targets['clean']"

	def __init__(self, role, exclude, warning_flags, repository_url):
		self._repository_url = repository_url
		self._warning_flags = warning_flags
		self._build_path = ".build"
		self._exclude = exclude
		self._cache = {}
		self._role = role

	def __getitem__(self, key):
		if not key in self._cache:
			if key == "show":
				self._cache[key] = fckit.BuildTarget(
					path = key,
					phony = True,
					on_build = lambda srcpaths: show(self._role))
			elif key == "init":
				self._cache[key] = fckit.BuildTarget(
					path = self._role.meta_path,
					on_build = lambda tgtpath, srcpaths: init_manifest(tgtpath))
			elif key == "clean":
				self._cache[key] = fckit.BuildTarget(
					path = key,
					phony = True,
					on_build = lambda srcpaths: clean(
						role = self._role,
						build_path = self._build_path))
			elif key == "dist":
				self._cache[key] = fckit.BuildTarget(
					path = os.path.join(self._build_path, "dist"),
					sources = get_dist_sources(
						role = self._role,
						exclude = self._exclude),
					on_build = True)
			elif key == "check":
				self._cache[key] = fckit.BuildTarget(
					path = os.path.join(self._build_path, "warnings.txt"),
					sources = [self["dist"]],
					on_build = lambda tgtpath, srcpaths: check(
						path = tgtpath,
						role = self._role,
						warning_flags = self._warning_flags))
			elif key == "package":
				self._cache[key] = fckit.BuildTarget(
					path = os.path.join(self._build_path, "%s-%s.tgz" % (self._role.name, self._role.version)),
					sources = [self["check"]],
					on_build = lambda tgtpath, srcpaths: package(
						path = tgtpath,
						role = self._role,
						exclude = self._exclude))
			elif key == "publish":
				self._cache[key] = fckit.BuildTarget(
					path = "publish",
					phony = True,
					sources = [self["package"]],
					on_build = lambda srcpath: publish(
						path = self["package"].path,
						url = self._repository_url))
			else:
				raise Error(key, "unknown target")
		return self._cache[key]

################################################################################
# entry point                                                                  #
################################################################################

def main(args = None):
	opts = docopt.docopt(
		doc = __doc__,
		argv = args)
	try:
		if opts["--no-color"]:
			fckit.disable_colors()
		if opts["--verbose"]:
			fckit.enable_tracing()
		if opts["--directory"]:
			fckit.chdir(opts["--directory"])
		role = Role()
		targets = Targets(
			role = role,
			exclude = opts["--exclude"].split(","),
			warning_flags = opts["--warnings"].split(","),
			repository_url = opts["--repository"])
		for key in opts["TARGETS"]:
			fckit.trace("at %s" % key)
			targets[key].build()
		if os.path.exists(targets["check"].path):
			with open(targets["check"].path, "r") as fp:
				print fckit.magenta(fp.read())
	except fckit.Error as exc:
		raise SystemExit(fckit.red(exc))
