# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

manifest = {
	"message": "missing 'owner' attribute, your file will be owned by the current ansible user",
	"predicate": lambda play: not "copy" in play or "owner" in play["copy"]
}
