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
  --no-color                  disable colored output
  -E                          convert warnings to errors

TARGET:
  * show     show role metadata
  * init     instantiate role template
  * dist     generate ansible distributable role files
  * clean    delete all generated files
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

import textwrap, glob, sys, os

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
	fckit.trace("writing", path)
	fckit.marshall(
		obj = obj,
		path = path,
		extname = extname,
		helpers = {
			".yml": _marshall_yaml,
		},
		overwrite = True)

class Role(object):

	def __init__(self, path = None):
		assert os.path.isdir(path), "not a directory"
		self.name = os.path.basename(os.path.abspath(path))
		self.dist_path = os.path.join(path, "dist")
		self.defaults_path = os.path.join(path, "defaults", "main.yml")
		self.readme_path = os.path.join(path, "README.md")
		self.meta_path = os.path.join(path, "meta", "main.yml")
		self.vars_path = os.path.join(path, "vars", "main.yml")
		self.maintask_path = os.path.join(path, "tasks", "main.yml")

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
	def package_path(self):
		return os.path.join(self.dist_path, "%s-%s.tgz" % (self.name, self.version))

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

###################
# build callbacks #
###################

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

def write_manifest(path):
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

def clean(role):
	path = os.path.dirname(role.package_path)
	if os.path.exists(path):
		fckit.remove(path)

def write_readme(role):
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
		"description": role.description,
		"platforms": role.platforms,
		"variables": role.variables,
		"name": role.name,
	})
	marshall(
		obj = text.encode("utf-8"),
		path = role.readme_path,
		extname = ".txt")

def write_maintask(role):
	raise NotImplementedError
	platforms = role.platforms
	tasks = []
	if platforms:
		tasks.append({
			"name": "assert the target platform is supported",
			"fail": {
				"msg": "unsupported platform -- please contact %s for support" % self.author,
			},
			"when": "ansible_distribution not in %s" % list(platform["name"] for platform in platforms),
		})
	for path in filter(lambda path: path != role.MAINTASK_PATH, glob.glob(os.path.join(role.TASKSDIR, "*.yml"))):
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
		path = role.MAINTASK_PATH)

def print_warning(*strings):
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
						print_warning(variable, "%s" % exc)
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
									print_warning("%s[%s]" % (path, name), "%s" % exc)

def package(role):
	if not os.path.exists(role.dist_path):
		fckit.mkdir(role.dist_path)
	fckit.check_call("tar", "czf", role.package_path, "--exclude", role.dist_path, ".")

def publish(path, url):
	fckit.check_call("curl", "-k", "-T", path, url)

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
		warning_flags = opts["--warnings"].split(",") if opts["--warnings"] else ()
		role = Role(opts["--directory"])
		##################
		# show lifecycle #
		##################
		show_phony_tgt = fckit.BuildTarget(
			path = "show",
			phony = True,
			callback = lambda sources: show(role))
		##################
		# init lifecycle #
		##################
		manifest_file_tgt = fckit.BuildTarget(
			path = role.meta_path,
			callback = lambda path, sources: write_manifest(path))
		###################
		# clean lifecycle #
		###################
		clean_phony_tgt = fckit.BuildTarget(
			path = "clean",
			phony = True,
			callback = lambda sources: clean(role))
		#####################
		# publish lifecycle #
		#####################
		readme_file_tgt = fckit.BuildTarget(
			path = role.readme_path,
			sources = (manifest_file_tgt,),
			callback = lambda path, sources: write_readme(role))
		maintask_file_tgt = fckit.BuildTarget(
			path = role.maintask_path,
			sources = (manifest_file_tgt,),
			callback = lambda path, sources: write_maintask(role))
		dist_phony_tgt = fckit.BuildTarget(
			path = "dist",
			phony = True,
			sources = (readme_file_tgt, maintask_file_tgt),
			callback = lambda sources: None)
		check_phony_tgt = fckit.BuildTarget(
			path = "check",
			phony = True,
			sources = (dist_phony_tgt,),
			callback = lambda sources: check(
				role = role,
				warning_flags = warning_flags))
		package_file_tgt = fckit.BuildTarget(
			path = role.package_path,
			callback = lambda path, sources: package(role))
		publish_phony_tgt = fckit.BuildTarget(
			path = "publish",
			phony = True,
			sources = (package_file_tgt,),
			callback = lambda sources: publish(sources[0], opts["--repository"]))
		switch = {
			"show": show_phony_tgt,
			"init": manifest_file_tgt,
			"dist": dist_phony_tgt,
			"clean": clean_phony_tgt,
			"check": check_phony_tgt,
			"package": package_file_tgt,
			"publish": publish_phony_tgt,
		}
		for target in opts["TARGETS"]:
			if target in switch:
				fckit.trace("at", target)
				switch[target].build()
			else:
				raise Error(target, "no such target")
	except fckit.Error as exc:
		raise SystemExit(fckit.red(exc))
