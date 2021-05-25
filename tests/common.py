from typing import Optional

__is_posix_value: Optional[bool] = None


def is_posix() -> bool:
    global __is_posix_value
    if __is_posix_value is None:
        try:
            import posix
            __is_posix_value = True
        except ImportError:
            __is_posix_value = False

        assert __is_posix_value is not None

    return __is_posix_value
