# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "manifest",
	"type": "role",
	"message": "missing platforms attribute, please specify the supported platforms",
	"predicate": lambda role, helpers: "platforms" in role.manifest["galaxy_info"],
}
