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

MANIFEST = {
	"flag": "layout",
	"type": "subdir",
	"message": "undefined role sub-directory",
	"predicate": lambda basename, helpers: basename in DEFINED,
}
