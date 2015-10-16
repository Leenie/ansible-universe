# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"type": "role",
	"message": "missing author attribute",
	"predicate": lambda role: "author" in role.manifest["galaxy_info"],
}
