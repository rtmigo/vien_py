import unittest

from vien._common import need_posix, NotPosixOsError


def is_posix_importable() -> bool:
    try:
        import posix
        return True
    except ImportError:
        return False


class Test(unittest.TestCase):
    def test_need_posix(self):
        if is_posix_importable():
            need_posix()  # no exception
        else:
            with self.assertRaises(NotPosixOsError):
                need_posix()
