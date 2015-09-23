
**Ansible-universe** is an [Ansible role](http://docs.ansible.com/ansible/playbooks_roles.html) build tool implementing the following features:
  * role syntax check
  * proper `README.md` generation
  * platform runtime check generation
  * role linter implementing best practices
  * packaging & publishing into private web repositories

It supports the following build targets:
  * `init` instantiate role template
  * `dist` generate ansible distributable role files
  * `check` include role in a dummy playbook and check syntax
  * `package` package role
  * `publish -r…` publish role to a web repository
  * `distclean` delete generated files


Build Manifest
--------------

**Ansible-universe** uses the native ansible-galaxy manifest, `meta/main.yml`, with the following additional attributes:
  * `version`, defaults to 0.0.1
  * `variables`, maps names to descriptions
  * `inconditions`, maps tasks filename to include conditions

On build, two files are generated:
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

Ansible Inc. has published a first set of [best practices][1] online, be sure to read them first.
The practices discussed here are complementing those official ones.

### P1. Playbook Interface

Always assume your playbook users are not developers:
design your playbooks to be configurable, through groups and variables set in the inventory and varfiles.
The inventory and varfiles are expected to be created/edited,
but having to modify a playbook to make it work is a mistake.

### P2. Role Interface

If you need a piece of provisioning more than once, re-design it as a role.
Roles are to Ansible what packages are to your platform or programming language.
You can safely assume that role users are actually developers,
as using them requires some more advanced Ansible skills — but, again, plan for configurability through variables.

### P3. Documentation

Given a playbook or a role, if groups or variables are not documented, they are non-existent.
Unfortunately, Ansible (as of version 1.9.2) has no mechanism to probe either groups or variables used in a playbook or role.
The documentation (generally the README.md file) is therefore the only learning medium for the users.

### P4. Role Repository

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
    within a range and include a subset of releases known as broken, e.g. (>=2.1, <4a0, !=2.4rc, != 2.5rc)
  * __Inefficient Binary Resources Storage__
    A playbook may contain binary resources (e.g. images or pre-compiled bytecode.)
    Storing those resources into a code repository is a bad practice (ref?.)

### P5. Validation

Validate your roles before publishing them.

### P6. Dependencies

Do not bundle any role with your playbook (or similarly, do not use git submodules):
use a requirements file and let Ansible handle its resolution (same principle than in any other stack: python, ruby, etc.)
A requirement file can reference a VCS or a web repository indifferently.

### P7. Naming

[Prefix][2]([bis][3]) all your playbook groups and variables by a short and unique ID (ideally the playbook name)
and [Prefix][2]([bis][3]) all your role variables by the role name as well.
Ansible only has a global namespace and having two identical variables will lead one to be overwritten by the other.
This is also true for handler names.

### P8. Isolation

Keep roles [self-contained][2].
Having shared variables between two roles is a design mistake.

### P9. Role Structure

Do not add any custom sub-directory to a role, this would result into an [undefined behavior][6].
As of version 1.9.2, 8 sub-directories are specified and used by the Ansible ecosystem:
  * defaults/
  * files/
  * handlers/
  * meta/
  * tasks/
  * templates/
  * vars/
  * library/

At any point in a future version, other sub-directories might be added
and if they are already used by your role for anything else, this will break.

### P10. Role Packaging

Fill-in your role metadata (meta/main.yml); among other things:
  * name
  * version (extended ansible-universe attribute),
  * authors
  * description
  * and the supported platforms (enforced by ansible-universe.)

<!-- REFERENCES -->
[1]: http://docs.ansible.com/ansible/playbooks_best_practices.html
[2]: https://openedx.atlassian.net/wiki/display/OpenOPS/Ansible+Code+Conventions
[3]: http://shop.oreilly.com/product/0636920035626.do
[4]: https://www.python.org/dev/peps/pep-0440/#version-specifiers
[5]: https://en.wikipedia.org/wiki/Principle_of_least_astonishment
[6]: https://en.wikipedia.org/wiki/Undefined_behavior
