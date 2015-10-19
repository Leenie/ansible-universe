# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "manifest",
	"type": "role",
	"message": "missing license attribute, please specify the role license",
	"predicate": lambda role, helpers: "license" in role.manifest["galaxy_info"],
}
