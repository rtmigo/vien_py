import os
import unittest
from pathlib import Path

from tests.common import is_posix
from tests.test_arg_parser import windows_too
from vien.main import get_project_dir
from vien.exceptions import PyFileArgNotFoundExit
from vien.arg_parser import Parsed


def fix_paths(s: str):
    if is_posix:
        s = s.replace('W:/', '/')
    return s


class TestGetProjectDir(unittest.TestCase):

    def setUp(self) -> None:
        os.chdir(os.path.dirname(__file__))

    def _gpd(self, cmd: str) -> Path:
        cmd = fix_paths(cmd)
        result = get_project_dir(Parsed(windows_too(cmd.split())))
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
        pd = self._gpd('-p W:/abc/def run python3 myfile.py')
        self.assertEqual(pd, Path(fix_paths('W:/abc/def')))

    def test_call_no_file(self):
        with self.assertRaises(PyFileArgNotFoundExit):
            self._gpd('-p W:/aa/bb/proj call python3 --version')

    def test_call_file_abs_proj_abs(self):
        pd = self._gpd('-p W:/aa/bb/proj call python3 W:/xx/yy/file.py')
        self.assertEqual(pd, Path(fix_paths('W:/aa/bb/proj')))

    def test_call_file_abs_proj_rel(self):
        pd = self._gpd('-p aa/bb/proj call python3 W:/xx/yy/file.py')
        self.assertEqual(pd, Path(fix_paths('W:/xx/yy/aa/bb/proj')))

    def test_call_file_abs_proj_rel_dots(self):
        pd = self._gpd('-p .. call python3 W:/abc/project/pkg/file.py')
        self.assertEqual(pd, Path(fix_paths('W:/abc/project')))

    def test_call_file_rel_proj_abs(self):
        pd = self._gpd('-p W:/aa/bb/proj call python3 xx/yy/file.py')
        self.assertEqual(pd, Path(fix_paths('W:/aa/bb/proj')))

    def test_call_file_rel_proj_rel(self):
        pd = self._gpd('-p aa/bb/proj call python3 xx/yy/file.py')
        self.assertEqual(pd, Path.cwd() / "xx" / "yy" / "aa" / "bb" / "proj")


if __name__ == "__main__":
    unittest.main()
