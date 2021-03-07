#!/bin/bash
set -e

echo "== SET UP VIRTUAL ENV =="

scriptParentDir="$(dirname "$(perl -MCwd -e 'print Cwd::abs_path shift' "$0")")"
cd "$scriptParentDir"

python3 -m venv ./temp_build_test_venv
source ./temp_build_test_venv/bin/activate

echo "== BUILDING & CHECKING =="

python3 -m pip install --upgrade pip
pip3 install setuptools wheel twine

python3 setup.py sdist bdist_wheel
twine check ./dist/* --strict

echo "== INSTALLING & RUNNING =="

unset -v latest_whl_file
for file in ./dist/*.whl; do
  [[ $file -nt latest_whl_file ]] && latest_whl_file=$file
done

pip3 install "$latest_whl_file" --force-reinstall

vien --help

echo "== TEARING DOWN =="

deactivate
python3 -m venv ./temp_build_test_venv --clear
rm -rf ./temp_build_test_venv
rm -rf ./build ./dist ./*.egg-info
