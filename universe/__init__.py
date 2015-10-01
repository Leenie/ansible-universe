# copyright (c) 2015 fclaerhout.fr, released under the MIT license.
# coding: utf-8

"""
Ansible role build tool.

Usage:
  ansible-universe [options] TARGETS...
  ansible-universe --help

Options:
  -W FLAGS, --warnings FLAGS  comma-separated list of flags to enable
  -C PATH, --directory PATH   set working directory
  -x PATHS, --exclude PATHS   comma-separated list of paths to ignore
  -r URL, --repository URL    set HTTP repository
  -m, --metadata              show role metadata
  -v, --verbose               output executed commands
  -h, --help                  display full help text
  --no-color                  disable colored output
  -E                          convert warnings to errors

TARGET:
  * init     instantiate role template
  * dist     generate ansible distributable role files
  * clean    delete all generated files
  * check    include role in a dummy playbook and check syntax
  * package  package role
  * publish  publish role to a web repository

Example:
  $ mkdir foo
  $ ansible-universe -C foo init dist check

Universe uses the ansible-galaxy manifest (meta/main.yml) with extra attributes:
  * prefix        variable prefix, defaults to rolename
  * version       role version
  * variables     maps names to descriptions
  * inconditions  maps tasks filename to include conditions
"""

import textwrap, glob, sys, os

import docopt, jinja2, fckit, yaml # 3rd-party

DEFAULTS_PATH = os.path.join("defaults", "main.yml")
README_PATH = "README.md"
META_PATH = os.path.join("meta", "main.yml")
VARS_PATH = os.path.join("vars", "main.yml")
TASKSDIR = "tasks"
MAINTASK_PATH = os.path.join(TASKSDIR, "main.yml")
DISTDIR = "dist"

MANIFESTS = tuple(dict({"name": name}, **__import__(name, globals()).MANIFEST) for name in (
	"task_has_no_remote_user",
	"template_has_owner",
	"copy_has_owner",
	"task_has_name"))

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
	fckit.trace("writing", path)
	fckit.marshall(
		obj = obj,
		path = path,
		extname = extname,
		helpers = {
			".yml": _marshall_yaml,
		},
		overwrite = True)

def warning(*strings):
	sys.stderr.write(fckit.magenta("WARNING! %s\n") % ": ".join(strings).encode("utf-8"))

class Role(object):
	"this object allows to fetch role information from various files"

	def __init__(self, directory = None):
		if directory:
			fckit.chdir(directory)
		self.name = os.path.basename(os.getcwd())

	def _get_manifest(self):
		"return role manifest as a dict"
		if not os.path.exists(META_PATH):
			raise Error("missing role manifest")
		return unmarshall(META_PATH)

	def _set_manifest(self, _dict):
		marshall(
			obj = _dict,
			path = META_PATH)

	manifest = property(_get_manifest, _set_manifest)

	def _get_version(self):
		try:
			return self.manifest["version"]
		except KeyError:
			raise Error("missing version attribute in manifest")

	def _set_version(self, string):
		self.manifest = dict(self.manifest, version = string)

	version = property(_get_version, _set_version)

	@property
	def galaxy_info(self):
		try:
			return self.manifest["galaxy_info"]
		except KeyError:
			raise Error("missing galaxy_info attribute in manifest")

	@property
	def author(self):
		try:
			return self.galaxy_info["author"]
		except KeyError:
			raise Error("missing author attribute in manifest")

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
		for key, value in (unmarshall(DEFAULTS_PATH) or {}).items():
			res[key] = {
				"description": None,
				"constant": False,
				"value": value,
			}
		for key, value in (unmarshall(VARS_PATH) or {}).items():
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
			raise Error("missing description attribute in manifest")

	@property
	def dependencies(self):
		"return list of role dependencies"
		return self.manifest.get("dependencies", ())

	@property
	def inconditions(self):
		"return dict mapping tasks/ playbooks to include conditions"
		return self.manifest.get("inconditions", {})

	def _generate_readme(self):
		template = """
			<!-- THIS IS A GENERATED FILE, DO NOT EDIT -->

			## {{ name }}
			
			{{ description or "(no description yet.)" }}


			## Supported Platforms

			{% for ptf in platforms %}  * {{ ptf.name }}
			{% else %}
			No supported platform specified (yet.)
			{% endfor %}

			## Variables

			| Name | Value | Constant? | Description |
			|------|-------|-----------|-------------|
			{% for k, v in variables.items() %}| {{ k }} | {{ v.value }} | {{ v.constant }} | {{ v.description }} |
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
			"description": self.description,
			"platforms": self.platforms,
			"variables": self.variables,
			"name": self.name,
		})
		marshall(
			obj = text.encode("utf-8"),
			path = README_PATH,
			extname = ".txt")

	def _generate_maintask(self):
		platforms = self.platforms
		tasks = []
		if platforms:
			tasks.append({
				"name": "assert the target platform is supported",
				"fail": {
					"msg": "unsupported platform -- please contact %s for support" % self.author,
				},
				"when": "ansible_distribution not in %s" % list(platform["name"] for platform in platforms),
			})
		for path in filter(lambda path: path != MAINTASK_PATH, glob.glob(os.path.join(TASKSDIR, "*.yml"))):
			name = path[len(TASKSDIR) + 1:]
			fckit.trace("including", name)
			if name in self.inconditions:
				tasks.append({
					"name": "%s is included" % name,
					"include": name,
					"when": self.inconditions[name],
				})
			else:
				tasks.append({
					"include": name,
				})
		marshall(
			obj = tasks,
			path = MAINTASK_PATH)

	def dist(self):
		for path, generate in {
			README_PATH: self._generate_readme,
			MAINTASK_PATH: self._generate_maintask,
		}.items():
			if not path in self.excluded_paths:
				generate()
			else:
				fckit.trace(path, "in excluded path, ignored")

	def check_manifest(self):
		manifest = self.manifest
		for key in (
			"version",
			"galaxy_info/author",
			"galaxy_info/license",
			"galaxy_info/platforms",
			"galaxy_info/description"):
			root = manifest["galaxy_info"] if key.startswith("/") else manifest
			if not os.path.basename(key) in root or not root[os.path.basename(key)]:
				warning(key, "missing manifest attribute")

	def check_syntax(self):
		"generate a playbook using the role and syntax-check it"
		tmpdir = fckit.mkdir()
		cwd = os.getcwd()
		fckit.chdir(tmpdir)
		try:
			# write playbook:
			playbook = [{
				"hosts": "127.0.0.1",
				"connection": "local",
				"roles": [self.name],
			}]
			marshall(
				obj = playbook,
				path = os.path.join(tmpdir, "playbook.yml"))
			# write inventory:
			inventory = "localhost ansible_connection=local"
			marshall(
				obj = inventory,
				path = os.path.join(tmpdir, "inventory.cfg"),
				extname = ".txt")
			# write configuration:
			config = {
				"defaults": {
					"roles_path": os.path.dirname(cwd),
					"hostfile": "inventory.cfg",
				}
			}
			marshall(
				obj = config,
				path = os.path.join(tmpdir, "ansible.cfg"))
			# perform the check:
			fckit.check_call("ansible-playbook", "playbook.yml", "--syntax-check")
		finally:
			fckit.chdir(cwd)
			fckit.remove(tmpdir)

###################
# build callbacks #
###################

def _init():
	fckit.mkdir(os.path.dirname(MAINTASK_PATH))
	fckit.mkdir(os.path.dirname(META_PATH))
	marshall(
		path = META_PATH,
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

def _clean(excluded_paths):
	for path in (MAINTASK_PATH, README_PATH, DISTDIR):
		if not path in excluded_paths and os.path.exists(path):
			fckit.remove(path)

def _check(variables, warning_flags):
	# manifest
	if not warning_flags or "manifest" in warning_flags:
		_check_manifest()
	# syntax
	if not warning_flags or "syntax" in warning_flags:
		_check_syntax()
	# readme
	if not warning_flags or "readme" in warning_flags:
		if not os.path.exists(README_PATH):
			raise Error(README_PATH, "missing documentation")
		with open(README_PATH, "r") as fp:
			text = fp.read()
			for key in variables:
				if not key in text:
					warning(key, "variable not documented in %s" % README_PATH)
	# naming
	if not warning_flags or "naming" in warning_flags:
		for key in role.variables:
			if not key.startswith(self.prefix):
				warning(key, "variable not properly prefixed, expected '%s' prefix" % self.prefix)
	# layout
	if not warning_flags or "layout" in warning_flags:
		for path in os.listdir("."):
			if os.path.isdir(path) and not path.startswith(".") and path not in (
				"defaults",
				"files",
				"handlers",
				"meta",
				"tasks",
				"templates",
				"vars",
				"library"):
				warning(path, "undefined role sub-directory")
	# linter
	manifests = tuple(manifest for manifest in MANIFESTS if not warning_flags or manifest["name"] in warning_flags)
	if manifests:
		for dirname, _, basenames in os.walk(TASKSDIR):
			for basename in basenames:
				_, extname = os.path.splitext(basename)
				if extname == ".yml":
					path = os.path.join(dirname, basename)
					fckit.trace("linting", path)
					tasks = unmarshall(path, default = []) or []
					for idx, task in enumerate(tasks):
						for manifest in manifests:
							if not manifest["predicate"](task):
								name = task.get("name", "task#%i" % (idx + 1))
								warning("%s[%s]" % (path, name), manifest["message"])

def _package(path):
	if not os.path.exists(DISTDIR):
		fckit.mkdir(DISTDIR)
	fckit.check_call("tar", "czf", path, "--exclude", DISTDIR, ".")

def _publish(package_path, repository_url):
	fckit.check_call("curl", "-k", "-T", package_path, repository_url)

##############
# entrypoint #
##############

def main(args = None):
	opts = docopt.docopt(
		doc = __doc__,
		argv = args)
	try:
		if opts["--no-color"]:
			fckit.disable_colors()
		if opts["--verbose"]:
			fckit.enable_tracing()
		if opts["-E"]:
			def warning(*strings):
				raise Error(": ".join(strings))
			globals()["warning"] = warning
		excluded_paths = () if not opts["--exclude"] else opts["--exclude"].split(",") # user files not to be overwritten
		warning_flags = opts["--warnings"].split(",") if opts["--warnings"] else ()
		role = Role(opts["--directory"])
		if opts["--metadata"]:
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
		check_tgt = fckit.BuildTarget(
			path = "check",
			phony = True,
			callback = lambda sources: _check(
				variables = role.variables,
				warning_flags = warning_flags))
		package_tgt = BuildTarget(
			path = os.path.join(DISTDIR, "%s-%s.tgz" % (role.name, role.version)),
			sources = (check_tgt,),
			callback = lambda path, sources: _package(path))
		switch = {
			"init": fckit.BuildTarget(
				path = "init",
				phony = True,
				callback = lambda sources: _init()),
			"dist": fckit.BuildTarget(
				path = "dist",
				phony = True,
				callback = role.dist),
			"clean": fckit.BuildTarget(
				path = "clean",
				phony = True,
				callback = lambda sources: _clean(excluded_paths)),
			"check": check_tgt,
			"package": package_tgt,
			"publish": fckit.BuildTarget(
				path = "publish",
				phony = True,
				sources = (package_tgt,),
				callback = lambda sources: _publish(sources[0], opts["--repository"])),
		}
		for target in opts["TARGETS"]:
			if target in switch:
				switch[target].build()
			else:
				raise Error(target, "no such target")
	except (fckit.Error, Error) as exc:
		raise SystemExit(fckit.red(exc))
