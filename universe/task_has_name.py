# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

def check(task, _):
	assert "name" in task, "missing 'name' attribute, please describe the target state"

MANIFEST = {
	"check_task": check,
}
