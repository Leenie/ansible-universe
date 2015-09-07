# REF: https://packaging.python.org

import setuptools

setuptools.setup(
	name = "ansible-universe", # https://www.python.org/dev/peps/pep-0426/#name
	version = "1.3.0", # https://www.python.org/dev/peps/pep-0440/
	packages = [
		"universe",
	], # https://pythonhosted.org/setuptools/setuptools.html#using-find-packages
	#description = "",
	#long_description = "",
	#url = "", # https://docs.python.org/2/distutils/setupscript.html#additional-meta-data
	#author = "",
	author_email = "code@fclaerhout.fr",
	license = "MIT",
	#classifiers = [], # https://pypi.python.org/pypi?%3Aaction=list_classifiers
	#keyword = [],
	#py_modules = [],
	install_requires = [
		"pyutils >=5,<9a0",
		"docopt",
		"PyYAML",
		"jinja2",
	], # https://packaging.python.org/en/latest/requirements.html#install-requires-vs-requirements-files
	#package_data = {}, # https://docs.python.org/2/distutils/setupscript.html#installing-package-data
	#data_files = {}, # https://docs.python.org/2/distutils/setupscript.html#installing-additional-files
	entry_points = {
		"console_scripts": [
			"ansible-universe=universe:main",
		],
	}, # https://pythonhosted.org/setuptools/setuptools.html#automatic-script-creation
	test_suite = "test",
	tests_require = [
		"pyutils >=5,<9a0",
		"docopt",
		"PyYAML",
		"jinja2",
	],
	#extra_require = {},
	#setup_requires = [],
	dependency_links = [
		"https://pypi.fclaerhout.fr/simple/pyutils",
	], # https://pythonhosted.org/setuptools/setuptools.html#dependencies-that-aren-t-in-pypi
	#scripts = [], # https://docs.python.org/2/distutils/setupscript.html#installing-scripts
)
