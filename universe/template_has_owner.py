# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"predicate": lambda task: not "template" in task or "owner" in task["template"],
	"message": "missing 'owner' attribute, your file will be owned by the current user",
}
