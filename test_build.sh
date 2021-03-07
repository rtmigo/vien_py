#!/bin/bash
set -e

## SET UP ####

scriptParentDir="$(dirname "$(perl -MCwd -e 'print Cwd::abs_path shift' "$0")")"
cd "$scriptParentDir"

## TEST ####

python3 setup.py sdist bdist_wheel
twine check ./dist/* --strict

## TEAR DOWN ####

rm -rf ./build ./dist ./*.egg-info
