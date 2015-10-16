# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"type": "role",
	"message": "missing version attribute",
	"predicate": lambda role: "version" in role.manifest,
}
