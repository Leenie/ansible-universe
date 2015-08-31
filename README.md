
**Ansible-Universe** is an Ansible Role build tool.
It wraps `ansible-galaxy` to add the missing bits:
  * platform check generation
  * role syntax check & linter
  * proper README.md generation
  * packaging & publishing into private http repositories

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