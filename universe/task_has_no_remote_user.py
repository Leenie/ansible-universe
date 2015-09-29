# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"predicate": lambda task: not "remote_user" in task,
	"message": "do not set a remote_user for a task, use sudo_*",
}
