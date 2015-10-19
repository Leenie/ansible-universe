# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

MANIFEST = {
	"type": "task",
	"message": "missing 'name' attribute, please describe the target state",
	"predicate": lambda task, helpers: "name" in task,
}
