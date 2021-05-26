import os
from typing import Optional

is_windows = os.name == 'nt'
is_posix = not is_windows


# __is_posix_value: Optional[bool] = None


class NotPosixOsError(Exception):
    pass


def need_posix():
    if not is_posix:
        raise NotPosixOsError
