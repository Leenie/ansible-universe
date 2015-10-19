# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

import os

import fckit # 3rd-party

def check_syntax(role, helpers):
	"generate a playbook using the role and syntax-check it"
	roles_path = os.path.dirname(os.path.abspath(role.path))
	tmpdir = fckit.mkdir()
	cwd = os.getcwd()
	fckit.chdir(tmpdir)
	try:
		# write playbook:
		playbook = [{
			"hosts": "127.0.0.1",
			"connection": "local",
			"roles": [role.name],
		}]
		helpers["marshall"](
			obj = playbook,
			path = os.path.join(tmpdir, "playbook.yml"))
		# write inventory:
		inventory = "localhost ansible_connection=local"
		helpers["marshall"](
			obj = inventory,
			path = os.path.join(tmpdir, "inventory.cfg"),
			extname = ".txt")
		# write configuration:
		config = {
			"defaults": {
				"roles_path": roles_path,
				"hostfile": "inventory.cfg",
			}
		}
		helpers["marshall"](
			obj = config,
			path = os.path.join(tmpdir, "ansible.cfg"))
		# perform the check:
		fckit.check_call("ansible-playbook", "playbook.yml", "--syntax-check")
		return True
	except:
		raise
		return False
	finally:
		fckit.chdir(cwd)
		fckit.remove(tmpdir)

MANIFEST = {
	"flag": "syntax",
	"type": "role",
	"message": "syntax error",
	"predicate": check_syntax,
}
