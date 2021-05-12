from importlib.machinery import SourceFileLoader
from pathlib import Path

from setuptools import setup, find_packages

constants = SourceFileLoader('constants', 'vien/constants.py').load_module()

# def readDocText():
#     """Reads README.md and returns the text after first empty line.
#     It helps to skip the header with badges intended only for GitHub.
#     """
#     doctext = (Path(__file__).parent / 'README.md').read_text()
#
#     # skipping until first empty line
#     lines = [l.strip() for l in doctext.splitlines()]
#     first_empty_line_index = lines.index("")
#     lines = lines[first_empty_line_index + 1:]
#
#     return "\n".join(lines)

readme = (Path(__file__).parent / 'README.md').read_text()
readme = "# " + readme.partition("\n#")[-1]

setup(
    name="vien",
    version=constants.__version__,

    author="Artëm IG",
    author_email="ortemeo@gmail.com",
    url='https://github.com/rtmigo/vien_py',

    packages=['vien'],
    install_requires=[],

    description="Command-line tool for managing Python virtual environments",

    long_description=readme,
    long_description_content_type='text/markdown',

    license=constants.__license__,

    entry_points={
        'console_scripts': [
            'vien = vien:main_entry_point',
        ]},

    keywords="virtual-environment venv virtualenv python command-line shell "
             "terminal bash run create delete execute".split(),

    # https://pypi.org/classifiers/
    classifiers=[

        # "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 3 - Alpha",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: BSD License',
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Environment :: Console",
        "Typing :: Typed",
        "Topic :: Software Development :: Build Tools",
        "Operating System :: POSIX",
    ],

    test_suite="test_unit.suite"
)
