# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

def check(variable, role):
	assert\
		variable.startswith(role.prefix),\
		"variable not properly prefixed,  -- expected '%s'" % role.prefix

MANIFEST = {
	"flag": "naming",
	"check_variable": check,
}
