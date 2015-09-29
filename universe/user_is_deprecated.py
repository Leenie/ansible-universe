# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"predicate": lambda task: not "user" in task,
	"message": "'user' has be renamed into 'remote_user' since Ansible 1.4",
}
