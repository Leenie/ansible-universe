# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"type": "task",
	"message": "do not set a remote_user for a task, use sudo_*",
	"predicate": lambda task, helpers: not "remote_user" in task,
}
