# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"type": "role",
	"message": "missing license attribute",
	"predicate": lambda role: "license" in role.manifest["galaxy_info"],
}
