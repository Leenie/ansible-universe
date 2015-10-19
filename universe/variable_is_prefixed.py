# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "naming",
	"type": "variable",
	"message": "unexpected variable prefix (you can change the expected prefix in the role manifest)",
	"predicate": lambda variable, helpers: variable.startswith(helpers["role"].prefix),
}
