# copyright (c) 2015 fclaerhout.fr, released under the MIT license.
# coding: utf-8

"""
Ansible role build tool.

Usage:
  ansible-universe [options] TARGETS...
  ansible-universe --help

Options:
  -W FLAGS, --warnings FLAGS  comma-separated list of flags to enable
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

MANIFESTS = tuple(dict({"name": name}, **__import__(name, globals()).MANIFEST) for name in ()) #FIXME

class Error(fckit.Error): pass

def unmarshall(path, default = None):
	"custom unmarshaller with yaml support"
	def _unmarshall_yaml(path):
		with open(path, "r") as fp:
			return yaml.load(fp)
	return fckit.unmarshall(
		path = path,
		default = default,
		helpers = {
			".yml": _unmarshall_yaml,
		})

def marshall(obj, path, extname = None):
	"custom marshaller with yaml support"
	def _marshall_yaml(obj, fp):
		yaml.dump(obj, fp, explicit_start = True, default_flow_style = False)
	fckit.marshall(
		obj = obj,
		path = path,
		extname = extname,
		helpers = {
			".yml": _marshall_yaml,
		},
		overwrite = True)

class Role(object):
	"helper object to parse role properties"

	def __init__(self, path = None):
		self.path = path
		self.name = os.path.basename(self.path)
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
		"return the list of supported platforms {'name':..., 'versions':...}"
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

def init_manifest(role):
	marshall(
		path = role.meta_path,
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

		{{ description or "(argh, no description yet.)" }}


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

def clean(targets, build_path):
	for tgt in targets:
		tgt.clean(purge = True)
	if os.path.exists(build_path):
		fckit.remove(build_path)

def warning(*strings):
	sys.stderr.write(fckit.magenta("WARNING! %s\n") % ": ".join(strings).encode("utf-8"))

def check(role, warning_flags):
	manifests = filter(
		lambda m: not warning_flags or m.get("flag", m["name"]) in warning_flags,
		MANIFESTS)
	if manifests:
		for variable in role.variables:
			for manifest in manifests:
				if "check_variable" in manifest:
					try:
						manifest["check_variable"](
							variable = variable,
							role = role)
					except AssertionError as exc:
						warning(variable, "%s" % exc)
		for dirname, _, basenames in os.walk(TASKSDIR):
			for basename in basenames:
				_, extname = os.path.splitext(basename)
				if extname == ".yml":
					path = os.path.join(dirname, basename)
					tasks = unmarshall(path, default = []) or []
					for idx, task in enumerate(tasks):
						for manifest in manifests:
							if "check_task" in manifest:
								try:
									manifest["predicate"](
										task = task,
										role = role)
								except AssertionError as exc:
									name = task.get("name", "task#%i" % (idx + 1))
									warning("%s[%s]" % (path, name), "%s" % exc)

def package(path, role):
	fckit.check_call("tar", "czf", path, "--exclude", os.path.dirname(path), role.path)

def publish(path, url):
	fckit.check_call("curl", "-k", "-T", path, url)

##############
# entrypoint #
##############

def get_source_targets(role, exclude):
	targets = {}
	# existing files:
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
	# files to generate if missing:
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

def get_target(key, role, exclude, _cache = {}):
	build_path = os.path.join(role.path, ".build")
	if not key in _cache:
		if key == "show":
			_cache[key] = fckit.BuildTarget(
				path = key,
				phony = True,
				on_build = lambda srcpaths: show(role))
		elif key == "init":
			_cache[key] = fckit.BuildTarget(
				path = role.meta_path,
				on_build = lambda tgtpath, srcpaths: init_manifest(role))
		elif key == "dist":
			_cache[key] = fckit.BuildTarget(
				path = os.path.join(build_path, "dist"),
				sources = get_source_targets(
					role = role,
					exclude = exclude),
				on_build = True)
		elif key == "clean":
			_cache[key] = fckit.BuildTarget(
				path = key,
				phony = True,
				on_build = lambda srcpaths: clean(
					targets = [get_target(
						key = "dist",
						role = role,
						exclude = exclude)],
					build_path = build_path))
		elif key == "package":
			_cache[key] = fckit.BuildTarget(
				path = os.path.join(build_path, "%s-%s.tgz" % (role.name, role.version)),
				on_build = lambda tgtpath, srcpaths: package(tgtpath, role))
		else:
			raise Error(key, "unknown target")
	return _cache[key]

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
		for key in opts["TARGETS"]:
			fckit.trace("at %s" % key)
			get_target(
				key = key,
				role = role,
				exclude = opts["--exclude"].split(",")).build()
	except fckit.Error as exc:
		raise SystemExit(fckit.red(exc))
