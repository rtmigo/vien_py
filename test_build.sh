#!/bin/bash
set -e

scriptParentDir="$(dirname "$(perl -MCwd -e 'print Cwd::abs_path shift' "$0")")"
cd "$scriptParentDir"

python3 setup.py sdist bdist_wheel
twine check ./dist/* --strict

# tear down
rm -rf ./build ./dist ./*.egg-info
