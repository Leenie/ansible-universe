# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

def check(variable, role):
	assert variable in role.readme, "variable not documented"

MANIFEST = {
	"flag": "readme",
	"check_variable": check,
}
