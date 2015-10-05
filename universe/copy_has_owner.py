# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

def check(task, _):
	assert\
		not "copy" in task or "owner" in task["copy"],\
		"missing 'owner' attribute, your file will be owned by the current user"

MANIFEST = {
	"check_task": check,
}
