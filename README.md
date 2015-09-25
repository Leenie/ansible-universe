
**Ansible-universe** is an [Ansible role](http://docs.ansible.com/ansible/playbooks_roles.html) build tool implementing the following features:
  * role syntax check
  * proper `README.md` generation
  * platform runtime check generation
  * role linter implementing best practices
  * packaging & publishing into private web repositories

The following _build targets_ are available:
  * `init` instantiate role template
  * `show` show role information
  * `dist` generate ansible distributable role files
  * `check` include role in a dummy playbook and check syntax
  * `package` package role
  * `publish -r…` publish role to a web repository
  * `distclean` delete generated files


Build Manifest
--------------

**Ansible-universe** uses the native ansible-galaxy manifest, `meta/main.yml`, with the following additional attributes:
  * `prefix`, defaults to rolename
  * `version`, defaults to 0.0.1
  * `variables`, maps names to descriptions
  * `inconditions`, maps tasks filename to include conditions

On `dist`, two files are generated:
  * `tasks/main.yml`, performing the platform check and including any other .yml file in tasks/
    Conditions to inclusions can be specified via the `inconditions` attribute of the manifest.
  * `README.md`, gathering the role description, supported platforms and data on variables.


Example
-------

	$ mkdir foo
	$ ansible-universe -C foo init dist check


Installation
------------

	$ pip install --user ansible-universe

or, if the PyPI repository is not available:

	$ pip install --user git+https://github.com/fclaerho/ansible-universe.git

The package will be installed in your [user site-packages](https://www.python.org/dev/peps/pep-0370/#specification) directory; make sure its `bin/` sub-directory is in your shell lookup path.

To uninstall:

	$ pip uninstall ansible-universe


Development Guide
-----------------

The builtin linter can easily be extended with your own checks:
  * in the universe directory, create a new module defining the `MANIFEST` dict
  * in `__init__.py`, register that new module in the `MANIFESTS` dict

The `MANIFEST` global has two attributes:
  * `message`, the message to display when the check fails
  * `predicate`, the callback — taking a `play`argument — used to do the actual check;


Appendix: Ansible Best Practices
--------------------------------

### GENERAL DESIGN RULES

#### Divide & Conquer

If you need a piece of provisioning more than once, re-design it as a role [1].
Roles are to Ansible what packages are to your platform or programming language.

#### Playbook Interface

Always assume your playbook users are not developers.
Design your playbooks to be configurable through groups and variables.
Users will use those in the inventory and varfiles.
The inventory and varfiles are expected to be created/edited, but making your user modify a playbook is a design mistake.

#### Role Interface

You can safely assume that role users are actually developers,
as using them requires some more advanced Ansible skills.
Design your roles to be configurable through variables.

#### Role Repository

Make your roles available either on a public VCS or on a public web repository.
Prefer web repository to avoid access control issues.
Indeed, contrary to other modern build stacks (e.g. Java, Python, Docker...),
Ansible does not offer any kind of package repository;
instead roles are simply “published” as code repositories (e.g. on github, etc.)
This entails major issues:
  * __Unexpected Access Restrictions__
    Code repositories are designed to enforce fine grained access control from the ground up;
    this means you have to explicitly be given access to a repository to use it.
    Package repositories have the opposite behavior: once published,
    a package is accessible to anyone (e.g. apt-get install, pip install...)
    except if configured otherwise (opt-in.) The intent is clear: on publication,
    the package is made available to everyone. Therefore, using a code repository as a package
    repository violates the UX [principle of least surprise][5].
  * __No Version Ordering & Expressions__
    A VCS uses an internal versioning system (e.g. a hash for git)
    which is not related to the “human readable” version strings (e.g. “v1.0.0”.)
    Version strings are generally tag names created manually by developers when necessary.
    As version strings are unusable by git and by extension, by ansible-galaxy,
    complex version expressions cannot be used when specifying a dependency.
    With other build tools, it is common for instance to request an compatible version of a dependency
    within a range and include a subset of releases known as broken, e.g. `>=2.1, <4a0, !=2.4rc, != 2.5rc`
  * __Inefficient Binary Resources Storage__
    A playbook may contain binary resources (e.g. images or pre-compiled bytecode.)
    Storing those resources into a code repository is a bad practice (REF?.)

#### Dependencies

Do not bundle any role with your playbook (or similarly, do not use git submodules):
use a requirements file and let Ansible handle its resolution.
The same principle applies to any build stack: python, java, ruby, etc.
For instance you do not bundle jar dependencies for a Java project.
A requirement file can reference a VCS or a web repository indifferently.

#### Isolation

Keep roles self-contained [2].
Having shared variables between two roles is a design mistake.

### FORMAL REQUIREMENTS

The following requirements are validated through the `check` target:

	$ cd myrole
	$ ansible-universe check

They are all validated by default (`-Wall`), switch on the ones you're interested in with the `-W` option.

#### Up-to-date Documentation, `-Wreadme`

Given a playbook or a role, if groups or variables are not documented, they are non-existent as,
unfortunately, Ansible (as of version 1.9.2) has no native mechanism to probe them.
The documentation (generally the `README.md` file) is therefore the only learning medium for the end-users.
Make sure it is up-to-date.

#### Naming, `-Wnaming`

Prefix all your playbook groups, playbook variables and role variables by a short and unique ID [2,3].
Ideally the playbook name if it fits.
Ansible only has a global namespace and having two identical variables will lead one to be overwritten by the other.
This is also true for handler names.

#### Directory Layout, `-Wlayout`

Do not add any custom sub-directory to a role or playbook, this would result into undefined behavior [6].

As of version 1.9.2:

**8** sub-directories are specified for a role [1]:
  * defaults/
  * files/
  * handlers/
  * meta/
  * tasks/
  * templates/
  * vars/
  * library/

**5** sub-directories are specified for a playbook [1]:
  * group_vars/
  * host_vars/
  * library/
  * filter_plugins/
  * roles/

At any point in a future version, other sub-directories might be added
and if they are already used by your role for anything else, this will break.

#### Role Packaging

Fill-in your role metadata (meta/main.yml); among other things:
  * name
  * version (extended ansible-universe attribute),
  * authors
  * description
  * and the supported platforms (enforced by ansible-universe.)

References
----------

  * 1 http://docs.ansible.com/ansible/playbooks_best_practices.html
  * 2 https://openedx.atlassian.net/wiki/display/OpenOPS/Ansible+Code+Conventions
  * 3 http://shop.oreilly.com/product/0636920035626.do
  * 4 https://www.python.org/dev/peps/pep-0440/#version-specifiers
  * 5 https://en.wikipedia.org/wiki/Principle_of_least_astonishment
  * 6 https://en.wikipedia.org/wiki/Undefined_behavior
