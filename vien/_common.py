import os

is_windows = os.name == 'nt'
is_posix = not is_windows


class NotPosixOsError(Exception):
    pass


def need_posix():
    if not is_posix:
        raise NotPosixOsError
