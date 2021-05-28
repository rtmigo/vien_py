# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

import os
from pathlib import Path
from typing import Union


def relative_fn_to_module_name(filename: str) -> str:
    if not filename.lower().endswith('.py'):
        raise ValueError("The filename does not end with '.py'.")
    filename = filename[:-3]
    if '.' in filename:
        raise ValueError("The filename contains dots.")
    if os.name == "nt":
        filename = filename.replace('\\', '/')
    assert not os.path.isabs(filename)
    # assert not filename.split()[0] == ".."
    return filename.replace('/', '.')


class NotInnerPath(ValueError):
    pass


def relative_inner_path(child: Union[str, Path],
                        parent: Union[str, Path]) -> str:
    """(/abc/parent/xyz/child, /abc/parent) -> xyz/child
    Not only returns the "relative" path, but also checks
    it is really relative.
    """
    rel_path = os.path.relpath(child, parent)

    first = rel_path.split(os.path.sep)[0]
    if first == ".." or first == "." or os.path.isabs(rel_path):
        raise NotInnerPath(f"The {child} is not a child of {parent}.")
    return rel_path