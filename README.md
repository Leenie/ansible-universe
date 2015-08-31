
**Ansible-Universe** is an Ansible Role build tool.
It wraps `ansible-galaxy` to add the missing bits:
  * platform check generation
  * role syntax check & linter
  * proper `README.md` generation
  * packaging & publishing into private http repositories


Build Manifest
--------------

**Ansible-universe** uses the ansible-galaxy manifest, `meta/main.yml`, with the following additional attributes:
  * `version`, defaults to 0.0.1
  * `variables`, maps names to descriptions
  * `inconditions`, maps tasks filename to include conditions

**Ansible-universe** generates two files:
  * `tasks/main.yml`, performing the platform check and including any other .yml file in tasks/
    Conditions to inclusions can be specified via the `inconditions` attribute of the manifest.
  * `README.md`, gathering the role description, supported platforms and data on variables.


Example
-------

	$ mkdir foo
	$ ansible-universe -C foo init dist check


Installation
------------

	$ pip install --user --extra-index-url https://pypi.fclaerhout.fr/simple/ ansible-universe

or, if that repository is not available:

	$ pip install --user git+https://github.com/fclaerho/ansible-universe.git

The package will be installed in your [user site-packages](https://www.python.org/dev/peps/pep-0370/#specification) directory; make sure its `bin/` sub-directory is in your shell lookup path.

To uninstall:

	$ pip uninstall ansible-universe


Linter Development
------------------

The builtin linter can easily be extended with your own checks:
  * in the universe directory, create a new module defining the `MANIFEST` dict
  * in `__init__.py`, register that new module in the `MANIFESTS` dict

The `MANIFEST` global has two attributes:
  * `message`, the message to display when the check fails
  * `predicate`, the callback to use to do the actual check;
     it should take a single argument `play` corresponding to the play being linted.
