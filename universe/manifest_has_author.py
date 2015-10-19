# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "manifest",
	"type": "role",
	"message": "missing author attribute, please specify the role author",
	"predicate": lambda role, helpers: "author" in role.manifest["galaxy_info"],
}
