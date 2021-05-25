import unittest
from pathlib import PosixPath, WindowsPath, Path

from vien._common import need_posix, NotPosixError

is_cwd_posix = isinstance(Path().cwd(), PosixPath)
is_cwd_windows = isinstance(Path().cwd(), WindowsPath)


class Test(unittest.TestCase):

    def test_need_posix(self):
        if is_cwd_posix:
            need_posix()  # no exception
        else:
            with self.assertRaises(NotPosixError):
                need_posix()
