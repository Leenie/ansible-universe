# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"type": "role",
	"message": "missing platforms attribute",
	"predicate": lambda role: "platforms" in role.manifest["galaxy_info"],
}
