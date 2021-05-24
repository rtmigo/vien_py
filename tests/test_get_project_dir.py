import os
import unittest
from pathlib import Path

from vien.main import get_project_dir
from vien.exceptions import PyFileArgNotFoundExit
from vien.arg_parser import Parsed


class TestGetProjectDir(unittest.TestCase):

    def setUp(self) -> None:
        os.chdir(os.path.dirname(__file__))

    def _gpd(self, cmd: str) -> Path:
        result = get_project_dir(Parsed(cmd.split()))
        self.assertTrue(result.is_absolute())
        return result

    def test_cwd_run(self):
        pd = self._gpd('run python3 myfile.py')
        self.assertEqual(pd, Path.cwd().absolute())

    def test_cwd_call(self):
        pd = self._gpd('call path/to/myfile.py')
        self.assertEqual(pd, Path.cwd().absolute())

    def test_run_relative(self):
        pd = self._gpd('-p abc/def run python3 myfile.py')
        self.assertEqual(pd, Path.cwd() / "abc" / "def")

    def test_run_absolute(self):
        pd = self._gpd('-p /abc/def run python3 myfile.py')
        self.assertEqual(pd, Path('/abc/def'))

    def test_call_no_file(self):
        with self.assertRaises(PyFileArgNotFoundExit):
            self._gpd('-p /aa/bb/proj call python3 --version')

    def test_call_file_abs_proj_abs(self):
        pd = self._gpd('-p /aa/bb/proj call python3 /xx/yy/file.py')
        self.assertEqual(pd, Path('/aa/bb/proj'))

    def test_call_file_abs_proj_rel(self):
        pd = self._gpd('-p aa/bb/proj call python3 /xx/yy/file.py')
        self.assertEqual(pd, Path('/xx/yy/aa/bb/proj'))

    def test_call_file_abs_proj_rel_dots(self):
        pd = self._gpd('-p .. call python3 /abc/project/pkg/file.py')
        self.assertEqual(pd, Path('/abc/project'))

    def test_call_file_rel_proj_abs(self):
        pd = self._gpd('-p /aa/bb/proj call python3 xx/yy/file.py')
        self.assertEqual(pd, Path('/aa/bb/proj'))

    def test_call_file_rel_proj_rel(self):
        pd = self._gpd('-p aa/bb/proj call python3 xx/yy/file.py')
        self.assertEqual(pd, Path.cwd() / "xx" / "yy" / "aa" / "bb" / "proj")


if __name__ == "__main__":
    unittest.main()
