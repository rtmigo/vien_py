#!/bin/bash

python3 -c '
import importlib.machinery;
print(
  importlib.machinery.SourceFileLoader("_", "vien/constants.py")
  .load_module().__version__)'