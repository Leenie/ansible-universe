# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"type": "task",
	"message": "missing 'owner' attribute, your file will be owned by the current user",
	"predicate": lambda task, role: not "copy" in task or "owner" in task["copy"],
}
