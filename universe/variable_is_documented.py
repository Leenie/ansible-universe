# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "readme",
	"type": "variable",
	"message": "variable not documented",
	"predicate": lambda variable, helpers: variable in helpers["role"].readme,
}
