# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"predicate": lambda task: not "copy" in task or "owner" in task["copy"],
	"message": "missing 'owner' attribute, your file will be owned by the current user",
}
