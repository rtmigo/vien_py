#!/usr/bin/env python3

from chkpkg import Package

if __name__ == "__main__":
    with Package() as pkg:
        pkg.run_shell_code('vien --help')

    print("\nPackage is OK!")

