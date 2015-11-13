# REF: https://packaging.python.org

import setuptools

requirements = (
	"docopt",
	"PyYAML",
	"jinja2",
	"fckit >=14.1.4, <15a0",
)

setuptools.setup(
	name = "ansible-universe", # https://www.python.org/dev/peps/pep-0426/#name
	version = "1.11.18", # https://www.python.org/dev/peps/pep-0440/
	packages = [
		"universe",
	], # https://pythonhosted.org/setuptools/setuptools.html#using-find-packages
	description = "Ansible role build tool",
	#long_description = "",
	url = "https://github.com/fclaerho/ansible-universe", # https://docs.python.org/2/distutils/setupscript.html#additional-meta-data
	author = "florent claerhout",
	author_email = "code@fclaerhout.fr",
	license = "MIT",
	#classifiers = [], # https://pypi.python.org/pypi?%3Aaction=list_classifiers
	#keyword = [],
	#py_modules = [],
	install_requires = requirements, # https://packaging.python.org/en/latest/requirements.html#install-requires-vs-requirements-files
	#package_data = {}, # https://docs.python.org/2/distutils/setupscript.html#installing-package-data
	#data_files = {}, # https://docs.python.org/2/distutils/setupscript.html#installing-additional-files
	entry_points = {
		"console_scripts": [
			"ansible-universe=universe:main",
		],
	}, # https://pythonhosted.org/setuptools/setuptools.html#automatic-script-creation
	test_suite = "test",
	tests_require = requirements,
	#extra_require = {},
	#setup_requires = [],
	#dependency_links = [], # https://pythonhosted.org/setuptools/setuptools.html#dependencies-that-aren-t-in-pypi
	#scripts = [], # https://docs.python.org/2/distutils/setupscript.html#installing-scripts
)
