# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "manifest",
	"type": "role",
	"message": "missing version attribute, please specify the role version",
	"predicate": lambda role, helpers: "version" in role.manifest,
}
