#!/bin/bash
set -e

# runs depz from source (when it is not installed)

thisFileParentDir="$(dirname "$(perl -MCwd -e 'print Cwd::abs_path shift' "$0")")"
cd "$thisFileParentDir"

python3 depz "$@"