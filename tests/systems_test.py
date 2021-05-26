import unittest

from vien._common import need_posix, UnexpectedOsError


def is_posix_importable() -> bool:
    try:
        import posix
        return True
    except ImportError:
        return False


class Test(unittest.TestCase):
    # as for now we assume there are only two OSes: POSIX and Windows

    def test_need_posix(self):
        if is_posix_importable():
            need_posix()  # no exception
        else:
            with self.assertRaises(UnexpectedOsError):
                need_posix()

    def test_need_windows(self):
        if is_posix_importable():
            with self.assertRaises(UnexpectedOsError):
                need_posix()
        else:
            need_posix() # no exception

