# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

import unittest, os

import universe, fckit # 3rd-party

fckit.enable_tracing()

class RoleTest(unittest.TestCase):

	def setUp(self):
		self.cwd = os.getcwd()
		self.tmpdir = fckit.mkdir()
		fckit.chdir(self.tmpdir)

	def tearDown(self):
		fckit.chdir(self.cwd)
		fckit.remove(self.tmpdir)

	def test(self):
		role = universe.Role()
		fckit.mkdir("meta")
		galaxy_info = {
			"author": "John Doe"
		}
		manifest = {
			"version": 42,
			"galaxy_info": galaxy_info,
		}
		universe.marshall(
			obj = manifest,
			path = role.meta_path)
		self.assertEqual(role.name, os.path.basename(self.tmpdir))
		self.assertEqual(role.get_manifest(), manifest)
		self.assertEqual(role.version, 42)
		self.assertEqual(role.galaxy_info, galaxy_info)
		self.assertEqual(role.author, galaxy_info["author"])

# files generated following 'init':
INITPATHS = ("meta/main.yml",)

# files generated following 'dist':
DISTPATHS = ("README.md", "tasks/main.yml")

class MainTest(unittest.TestCase):

	def _main(self, *args):
		universe.main(("-v", "-C", self.tmpdir) + args)

	def _assert_path_state(self, path, present = True):
		path = os.path.join(self.tmpdir, path)
		func = self.assertTrue if present else self.assertFalse
		func(os.path.exists(path), "%s: %s" % (
			path,
			"absent, expected present" if present else "present, expected absent"))

	def setUp(self):
		self.cwd = os.getcwd()
		self.tmpdir = fckit.mkdir()

	def tearDown(self):
		fckit.chdir(self.cwd)
		fckit.remove(self.tmpdir)

	def test_init(self):
		self._main("init")
		map(self._assert_path_state, INITPATHS)

	def test_init_package_clean(self):
		self._main("init", "package")
		for path in INITPATHS + DISTPATHS:
			self._assert_path_state(path)
		pkgpath = os.path.join(self.tmpdir, ".build", "%s-0.0.1.tgz" % os.path.basename(self.tmpdir))
		self._assert_path_state(pkgpath)
		self._main("clean")
		for path in INITPATHS:
			self._assert_path_state(path)
		for path in DISTPATHS:
			self._assert_path_state(path, present = False)
		self._assert_path_state(pkgpath, present = False)

if __name__ == "__main__": unittest.main(verbosity = 2)
