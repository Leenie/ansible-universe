# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

DEFINED = (
	"defaults",
	"files",
	"handlers",
	"meta",
	"tasks",
	"templates",
	"vars",
	"library")

def check(subdir, _):
	assert subdir in DEFINED, "undefined role sub-directory"

MANIFEST = {
	"check_subdir": check,
}
