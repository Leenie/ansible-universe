# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

def check(task, _):
	assert not "remote_user" in task, "do not set a remote_user for a task, use sudo_*"

MANIFEST = {
	"check_task": task,
}
