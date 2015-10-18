# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "naming",
	"type": "variable",
	"message": "variable not properly prefixed,  -- expected '%s'" % role.prefix,
	"predicate": lambda variable, role: variable.startswith(role.prefix),
}
