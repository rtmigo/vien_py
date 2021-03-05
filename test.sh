#!/bin/bash
set -e

scriptParentDir="$(dirname "$(perl -MCwd -e 'print Cwd::abs_path shift' "$0")")"
cd "$scriptParentDir"

python3 -m unittest discover -t . -s "depz" -p "*.py" --buffer

# to run tests on particular file:
# python3 -m unittest discover -t . -s "depz" -p filename.py

