# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "owner",
	"type": "task",
	"message": "missing 'owner' attribute, the file will be owned by the varying current user",
	"predicate": lambda task, helpers: not "copy" in task or "owner" in task["copy"],
}
