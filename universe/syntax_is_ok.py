# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

import os

import fckit # 3rd-party

def check_syntax(role):
	"generate a playbook using the role and syntax-check it"
	role_path = os.path.abspath(role.path)
	tmpdir = fckit.mkdir()
	fckit.chdir(tmpdir)
	try:
		# write playbook:
		playbook = [{
			"hosts": "127.0.0.1",
			"connection": "local",
			"roles": [role.name],
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
				"roles_path": role_path,
				"hostfile": "inventory.cfg",
			}
		}
		marshall(
			obj = config,
			path = os.path.join(tmpdir, "ansible.cfg"))
		# perform the check:
		fckit.check_call("ansible-playbook", "playbook.yml", "--syntax-check")
		return True
	finally:
		fckit.chdir(cwd)
		fckit.remove(tmpdir)
		return False

MANIFEST = {
	"flag": "syntax",
	"type": "role",
	"message": "syntax error",
	"predicate": check_syntax,
}
