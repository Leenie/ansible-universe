# copyright (c) 2015 fclaerhout.fr, released under the MIT license.
# coding: utf-8

"""
Ansible role build tool.

Usage:
  ansible-universe [options] TARGETS...
  ansible-universe --help

Options:
  -C PATH, --directory PATH  set working directory
  -r URL, --repository URL   set HTTP repository
  -x PATHS, --exclude PATHS  comma-separated list of paths to ignore
  -v, --verbose              output executed commands
  -h, --help                 display full help text
  --no-color                 disable colored output
  -a, --all                  with clean, remove distdir

TARGET:
  * init         instantiate role template
  * show         show role information
  * dist         generate ansible distributable role files
  * check        include role in a dummy playbook and check syntax
  * package      package role
  * publish -r…  publish role to a web repository
  * distclean    delete generated files

Example:
  $ mkdir foo
  $ ansible-universe -C foo init dist check

Universe uses the ansible-galaxy manifest (meta/main.yml) with extra attributes:
  * prefix        variable prefix, defaults to rolename
  * version       role version
  * variables     maps names to descriptions
  * inconditions  maps tasks filename to include conditions
"""

import textwrap, glob, time, sys, os

import docopt, jinja2, fckit, yaml # 3rd-party

DEFAULTS_PATH = os.path.join("defaults", "main.yml")
README_PATH = "README.md"
META_PATH = os.path.join("meta", "main.yml")
VARS_PATH = os.path.join("vars", "main.yml")
TASKSDIR = "tasks"
MAINTASK_PATH = os.path.join(TASKSDIR, "main.yml")
DISTDIR = "dist"

MANIFESTS = tuple(dict({"name": name}, **__import__(name, globals()).MANIFEST) for name in (
	"copy_has_owner",
	"play_has_name"))

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
	sys.stderr.write(fckit.yellow("warning! %s\n") % ": ".join(strings))

class Role(object):

	def __init__(self, excluded_paths = None, directory = None):
		self.excluded_paths = excluded_paths or () # user files not to be overwritten
		if directory:
			fckit.chdir(path)
		self.name = os.path.basename(os.getcwd())

	def _get_manifest(self):
		"return role manifest as a dict"
		return unmarshall(META_PATH)

	def _set_manifest(self, _dict):
		marshall(
			obj = _dict,
			path = META_PATH)

	manifest = property(_get_manifest, _set_manifest)

	def _get_version(self):
		"return role version"
		return self.manifest["version"]

	def _set_version(self, string):
		self.manifest = dict(self.manifest, version = string)

	version = property(_get_version, _set_version)

	@property
	def author(self):
		"return role author"
		return self.manifest["galaxy_info"]["author"]

	@property
	def prefix(self):
		"return prefix for variables, defaults on role name"
		return self.manifest.get("prefix", "%s_" % self.name.lower().replace("-", "_"))

	@property
	def platforms(self):
		"return the list of supported platforms {'name':..., 'versions':...}"
		return self.manifest["galaxy_info"].get("platforms", ())

	@property
	def variables(self, _cache = {}):
		"return dict mapping variable names to {'constant', 'default', 'description'}"
		if not _cache:
			for key, value in (unmarshall(DEFAULTS_PATH) or {}).items():
				_cache[key] = {
					"description": None,
					"constant": False,
					"value": value,
				}
			for key, value in (unmarshall(VARS_PATH) or {}).items():
				if key in _cache:
					raise Error(key, "variable both set in vars/ and defaults/")
				else:
					_cache[key] = {
						"description": None,
						"constant": True,
						"value": value,
					}
			for key, value in self.manifest.get("variables", {}).items():
				if key in _cache:
					_cache[key]["description"] = value
				else:
					_cache[key] = {
						"description": value,
						"constant": False,
						"value": None,
					}
		return _cache

	@property
	def description(self):
		"return role description"
		return self.manifest["galaxy_info"]["description"]

	@property
	def dependencies(self):
		"return list of role dependencies"
		return self.manifest["dependencies"]

	@property
	def inconditions(self):
		"return dict mapping tasks/ playbooks to include conditions"
		return self.manifest.get("inconditions", {})

	def init(self):
		"use ansible-galaxy to populate current directory"
		tmpdir = "_temp"
		fckit.check_call("ansible-galaxy", "init", tmpdir, "--force")
		for path in (README_PATH, MAINTASK_PATH):
			fckit.remove(os.path.join(tmpdir, path))
		for basename in os.listdir(tmpdir):
			os.rename(os.path.join(tmpdir, basename), basename)
		fckit.remove(tmpdir)
		self.version = "0.0.1"

	def show(self):
		print yaml.dump(
			data = {
				"name": self.name,
				"author": self.author,
				"version": self.version,
				"platforms": self.platforms,
				"variables": self.variables, 
				"description": self.description
			},
			explicit_start = True,
			default_flow_style = False)

	def _generate_readme(self):
		template = """
			<!-- THIS IS A GENERATED FILE, DO NOT EDIT -->

			**{{ name }}** — {{ description or "No description (yet.)" }}


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
		mainplays = []
		author = self.author or "the role author"
		if platforms:
			mainplays.append({
				"name": "assert the target platform is supported",
				"fail": {
					"msg": "unsupported platform -- please contact %s for support" % author,
				},
				"when": "ansible_distribution not in %s" % list(platform["name"] for platform in platforms),
			})
		for path in filter(lambda path: path != MAINTASK_PATH, glob.glob(os.path.join(TASKSDIR, "*.yml"))):
			name = path[len(TASKSDIR) + 1:]
			fckit.trace("including", name)
			if name in self.inconditions:
				mainplays.append({
					"include": name,
					"when": self.inconditions[name],
				})
			else:
				mainplays.append({
					"include": name,
				})
		marshall(
			obj = mainplays,
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
			fckit.trace("check passed")
		finally:
			fckit.chdir(cwd)
			fckit.remove(tmpdir)

	def check_naming(self):
		for key in self.variables:
			if not key.startswith(self.prefix):
				warning(key, "variable name is not properly prefixed (%s)" % self.prefix)

	def check_layout(self):
		for path in os.listdir("."):

	def lint(self):
		for dirname, _, basenames in os.walk(TASKSDIR):
			for basename in basenames:
				_, extname = os.path.splitext(basename)
				if extname == ".yml":
					path = os.path.join(dirname, basename)
					fckit.trace("linting '%s'" % path)
					tasks = unmarshall(path, default = []) or []
					for idx, play in enumerate(tasks):
						for manifest in MANIFESTS:
							if not manifest["predicate"](play):
								name = play.get("name", "play#%i" % (idx + 1))
								warning("%s[%s]" % (path, name), manifest["message"])

	def check(self, syntax = True, naming = True, lint = True):
		self.check_syntax()
		self.check_naming()
		self.lint()

	def _get_package_path(self):
		"return distribution package path"
		basename = "%s-%s.tgz" % (self.name, self.version)
		return os.path.join(DISTDIR, basename)

	def package(self):
		if not os.path.exists(DISTDIR):
			fckit.mkdir(DISTDIR)
		fckit.check_call("tar", "czf", self._get_package_path(), "--exclude", DISTDIR, ".")

	def publish(self, repository_url):
		if not repository_url:
			raise Error("no repository")
		fckit.check_call(("curl", "-k", "-T", self._get_package_path(), repository_url))

	def distclean(self):
		for path in (MAINTASK_PATH, README_PATH, DISTDIR):
			if not path in self.excluded_paths and os.path.exists(path):
				fckit.remove(path)

def main(args = None):
	opts = docopt.docopt(
		doc = __doc__,
		argv = args)
	try:
		if opts["--no-color"]:
			fckit.disable_colors()
		if opts["--verbose"]:
			fckit.enable_tracing()
		role = Role(
			excluded_paths = (opts["--exclude"] or "").split(","),
			directory = opts["--directory"])
		switch = {
			"init": role.init,
			"show": role.show,
			"dist": role.dist,
			"check": role.check,
			"package": role.package,
			"publish": lambda: role.publish(opts["--repository"]),
			"distclean": role.distclean,
		}
		for target in opts["TARGETS"]:
			if target in switch:
				switch[target]()
			else:
				raise Error(target, "no such target")
	except (fckit.Error, Error) as exc:
		raise SystemExit(fckit.red(exc))
