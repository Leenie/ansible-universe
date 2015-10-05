# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

def check(role):
	manifest = self.manifest
	for key in (
		"version",
		"galaxy_info/author",
		"galaxy_info/license",
		"galaxy_info/platforms",
		"galaxy_info/description"):
		root = manifest["galaxy_info"] if key.startswith("/") else manifest
		if not os.path.basename(key) in root or not root[os.path.basename(key)]:
			warning(key, "missing manifest attribute")

MANIFEST = {
	"check_role": role,
}