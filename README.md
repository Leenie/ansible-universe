
**Ansible-universe** is an [Ansible role](http://docs.ansible.com/ansible/playbooks_roles.html) build tool implementing the following features:
  * Role syntax check
  * Proper `README.md` generation
  * Role [linter][9] implementing best practices
  * Packaging & publishing into private web (DAV) repositories
  * Proper `tasks/main.yml` generation, with platforms runtime check

The following [build targets][7] are supported:
  * `init`     instantiate role template
  * `show`     show role information
  * `dist`     generate ansible distributable role files
  * `clean`    delete all generated files
  * `check`    include role in a dummy playbook and check syntax
  * `package`  package role
  * `publish`  publish role to a web repository

The following [lifecycles][7] are supported:
  * **`init`**
  * **`show`**
  * **`clean`**
  * **`publish`** < `package` < `check` < `dist`

**Ansible-universe** uses the ansible-galaxy [build manifest][7] (`meta/main.yml`) with extra attributes:
  * `prefix`, variable prefix, defaults to rolename
  * `version`, defaults to 0.0.1
  * `variables`, maps names to descriptions
  * `include_when`, maps `tasks/` filenames to include conditions


Example
-------

	$ mkdir foo
	$ ansible-universe -C foo init check


Tutorial
--------

For this tutorial, we consider a simple use case: a role managing an `nginx` service.

A role is a directory containing various assets, the first step is therefore to create that directory:

	$ mkdir nginx

Let's initialize the role with **Ansible-universe**:

	$ ansible-universe -C nginx init

The `init` target creates a dummy (ansible-galaxy) role manifest: `meta/main.yml`.
This manifest is also the build manifest for **Ansible-universe**.
This is actually the only required file for distributing a role.
Take some time to edit this file:
  * set the author (you)
  * set a description
  * select supported platforms (Debian and Ubuntu in our case)
  * etc.

You are then free to fill-in the other directories depending on your role.
Remember only 8 sub-directories are specified,
for further details, please check the Directory Layout section of the best practices, in the appendix.

As for this tutorial, we only need the `tasks/` sub-directory.
This directory contains a single file for now, named `nginx.yml`:

	$ cat > tasks/nginx.yml <<EOF
	---
	- apt:
	    name: nginx
	    state: present
	- service:
	    name: nginx
	    state: started
	    enabled: yes
	-
	EOF

Let's call **Ansible-universe** to generate and check everything:

	$ ansible-universe -C nginx check -v
	generating nginx/tasks/main.yml
	generating nginx/README.md

	playbook: playbook.yml

	ERROR: expecting dict; got: None, error in /tmp/nginx/tasks/nginx.yml
	** WARNING: syntax error
	   source: role 'nginx'
	   flag: syntax
	** WARNING: missing 'name' attribute, please describe the target state
	   source: task 'nginx.yml[#2]'
	   flag: task_has_name

As indicated in the `lifecycle` section, the `check` target implies `dist`, which is called first.

On `dist`, two files are generated:
  * `tasks/main.yml`, performing the platform check and including any other YAML file in `tasks/`.
    Conditions to inclusions can be specified via the `include_when` attribute of the manifest.
  * `README.md`, gathering the role description, supported platforms and data on variables.

On `check`, all checks are run, and in the above example, 2 warnings were raised.
A syntax error was detected, let's fix it by removing the last dash in `tasks/nginx.yml`.
The other warning says that we didn't describe one of our tasks, add a name attribute to fix it.
Re-run **Ansible-universe**, you should get the following layout with no warning:

	$ tree nginx/
	nginx/
	├── meta
	│   └── main.yml
	├── README.md
	└── tasks
	    ├── main.yml
	    └── nginx.yml

Your role is now ready to be distributed.
If you're using a VCS as repository, simply commit and push the files,
but remember to exclude the build byproducts (`*.hmap`, `.build`.)
If you're using a web repository, proceed as follow (set a working repository URL beforehand):

	$ ansible-universe -C nginx publish -r http://somewhere
	generating nginx/.build/nginx-0.0.1.tgz
	./README.md
	./meta/main.yml
	./tasks/main.yml
	./tasks/nginx.yml
	publishing nginx/.build/nginx-0.0.1.tgz to http://somewhere


Installation
------------

	$ pip install --user ansible-universe

To uninstall:

	$ pip uninstall ansible-universe


Development Guide
-----------------

The built-in [linter][9] can easily be extended with your own checks:
  * in the universe directory, create a new module defining the `MANIFEST` global dict
  * in `__init__.py`, register that new module by its name in the `MANIFESTS` dict

In your module, the `MANIFEST` dictionary shall contains the following attributes:
  * Required `type`: either `role`, `variable`, `subdir` or `task`.
    This specify the objects that will be passed to the predicate below.
  * Required `predicate`: a callback with two parameters (object, helpers) and returning a Boolean.
    `helpers` is a dictionary containing various functions and objects: `role`, `marshall()`.
  * Required `message`: the message to display when the predicate is violated.
  * Optional `flag`: default to module name, symbol used with the `-W` command line option.


Appendix: Ansible Best Practices
--------------------------------

### GENERAL DESIGN RULES

#### Divide & Conquer

If you need a piece of provisioning more than once, re-design it as a [role][1].
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
    [version expressions][4] cannot be used when specifying a dependency.
    With other build tools, it is common for instance to request an compatible version of a dependency
    within a range and exclude a subset of releases known as broken, e.g. `>=2.1, <4a0, !=2.4rc, != 2.5rc`
  * __Inefficient Binary Resources Storage__
    A playbook may contain binary resources (e.g. images or pre-compiled bytecode.)
    Storing those resources into a code repository is a bad practice (REF?.)

#### Dependencies

Do not bundle any role with your playbook (or similarly, do not use git submodules):
use a requirements file and let ansible-galaxy handle its resolution.
The same principle applies to any build stack: python, java, ruby, etc.
For instance you do not bundle jar dependencies for a Java project.
A requirement file can reference a VCS or a web repository indifferently.

#### Isolation

Keep roles [self-contained][2].
Having shared variables between two roles is a design mistake.
Instead make your roles configurable via variables and handle integration issues in the corresponding play.

### FORMAL REQUIREMENTS

The following requirements are all validated by default via the `check` target:

	$ cd myrole
	$ ansible-universe check

You can switch on only the ones you're interested in with the `-W<flag>,…` option.

#### Manifest, `-Wmanifest`

Make sure your role manifest contains the [required][8] information for publication:

  * Version (extended attribute),
  * Authors
  * License
  * Description
  * Supported platforms

#### Documentation, `-Wreadme`

Given a playbook or a role, if groups or variables are not documented, they are non-existent as,
unfortunately, Ansible (as of version 1.9.2) has no native mechanism to probe them.
The documentation (generally the `README.md` file) is therefore the only learning medium for the end-users.
[Make sure your documentation it is up-to-date][8].

#### Naming, `-Wnaming`

[Prefix][2] ([bis][3], [rebis][8]) all your playbook groups, playbook variables and role variables by a short and unique ID.
Ideally the playbook name if it fits.
Ansible only has a global namespace and having two identical variables will lead one to be overwritten by the other.
This is also true for handler names.

#### Directory Layout, `-Wlayout`

Do not add any custom sub-directory to a role or playbook, this would lead to [undefined behavior][6]:
at any point in a future version, other sub-directories might be needed by Ansible
and if they are already used by your role for anything else, this will break.

As of Ansible version 1.9.2, **8** sub-directories are [specified][1] for a role:
  * `defaults/`
  * `files/`
  * `handlers/`
  * `meta/`
  * `tasks/`
  * `templates/`
  * `vars/`
  * `library/`

And **5** sub-directories are [specified][1] for a playbook:
  * `group_vars/`
  * `host_vars/`
  * `library/`
  * `filter_plugins/`
  * `roles/`

#### Name task, `-Wtask_has_name`

Make the intent of each task explicit by setting its `name` attribute.

#### Do not set a Remote User, `-Wtask_has_no_remote_user`

It's tempting to always assume your playbooks/roles are run as root and to enforce it by setting `remote_user`.
This is a bad idea as your users might want to use another user that has equivalent privileges (e.g. via sudo.)
The root account is often disabled on modern systems for security reasons.
If you need an explicit user for a given task, use `sudo_user: <name>` and `sudo: yes`.

#### On copy/template, Set a owner, `-Wowner`

If no owner is specified on a `copy` or a `template` task, the current user UID will be used.
But that user can change and so will the file owner depending on who is running the playbook.
This violates the idempotence rule.


<!-- references -->

[1]: http://docs.ansible.com/ansible/playbooks_best_practices.html
[2]: https://openedx.atlassian.net/wiki/display/OpenOPS/Ansible+Code+Conventions
[3]: http://shop.oreilly.com/product/0636920035626.do
[4]: https://www.python.org/dev/peps/pep-0440/#version-specifiers
[5]: https://en.wikipedia.org/wiki/Principle_of_least_astonishment
[6]: https://en.wikipedia.org/wiki/Undefined_behavior
[7]: https://github.com/fclaerho/buildstack#glossary
[8]: https://galaxy.ansible.com/intro#share
[9]: https://en.wikipedia.org/wiki/Lint_(software)
