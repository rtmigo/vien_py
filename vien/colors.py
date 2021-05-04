# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause


import unittest


def color_escape(s: str):
    esc_open = r"\[\e[;"  # r"\e[" is not enough! https://superuser.com/a/367280
    # esc_open = r"\[\e[;"  # r"\e[" is not enough! https://superuser.com/a/367280
    esc_close = r"\]"

    return f"{esc_open}{s}{esc_close}"


class TestColorEscape(unittest.TestCase):
    def test(self):
        # it's easy to lose significant backslashes so
        self.assertEqual(color_escape("inner"), r"\[\e[;inner\]")


class Colors:
    GREEN = color_escape("32m")
    MAGENTA = color_escape("35m")
    YELLOW = color_escape("33m")
    CYAN = color_escape("36m")
    BLUE = color_escape("34m")
    NOCOLOR = color_escape("0m")
