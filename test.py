# copyright (c) 2015 fclaerhout.fr, all rights reserved

import unittest, os

import utils, universe # 3rd-party

# files generated following 'init':
INITPATHS = ("meta/main.yml", "handlers/main.yml", "defaults/main.yml")

# files generated following 'dist':
DISTPATHS = ("README.md", "tasks/main.yml")

class Test(unittest.TestCase):

	def _main(self, *args):
		universe.main(("-v", "-C", self.tmpdir) + args)

	def setUp(self):
		self.tmpdir = utils.mkdir()
		self._main("init")

	def tearDown(self):
		utils.remove(self.tmpdir)

	def _assert_path_state(self, path, present = True):
		path = os.path.join(self.tmpdir, path)
		func = self.assertTrue if present else self.assertFalse
		func(os.path.exists(path), "%s: invalid state" % path)

	def test_init(self):
		map(self._assert_path_state, INITPATHS)

	def test_dist_distclean(self):
		self._main("dist")
		map(self._assert_path_state, INITPATHS + DISTPATHS)
		self._main("distclean")
		map(self._assert_path_state, INITPATHS)
		map(lambda path: self._assert_path_state(path, present = False), DISTPATHS)

	def test_dist_check(self):
		self._main("dist", "check")

	def test_package(self):
		self._main("package")
		path = os.path.join(self.tmpdir, "dist", "%s-0.0.1.tgz" % os.path.basename(self.tmpdir))
		self._assert_path_state(path)

if __name__ == "__main__": unittest.main(verbosity = 2)
