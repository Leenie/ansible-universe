# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

	def check_syntax(self):
		"generate a playbook using the role and syntax-check it"
		tmpdir = fckit.mkdir()
		cwd = os.getcwd()
		fckit.chdir(tmpdir)
		try:
			# write playbook:
			playbook = [{
				"hosts": "127.0.0.1",
				"connection": "local",
				"roles": [self.name],
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
					"roles_path": os.path.dirname(cwd),
					"hostfile": "inventory.cfg",
				}
			}
			marshall(
				obj = config,
				path = os.path.join(tmpdir, "ansible.cfg"))
			# perform the check:
			fckit.check_call("ansible-playbook", "playbook.yml", "--syntax-check")
		finally:
			fckit.chdir(cwd)
			fckit.remove(tmpdir)