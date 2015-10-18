# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"flag": "readme",
	"type": "variable",
	"message": "variable not documented",
	"check_variable": lambda variable, role: variable in role.readme,
}
