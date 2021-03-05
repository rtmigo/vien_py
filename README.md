# [vep](https://github.com/rtmigo/vep)

[![Generic badge](https://img.shields.io/badge/ready_for_use-no-red.svg)](#)

Command-line shortcuts for Python virtual environments.

# Why

Switching between different projects in Python should be simple. I needed a short command 
that I would type even half asleep.

Not something like
```base
$ source /where/is/that/damn/directory/.venv/bin/activate
```

But something like
```base
$ cd /abc/myproject
$ vep shell
```

# What is does

`vep` offers a simple rule of where to place the virtualenv.

For a Python project located in directory `aaa` the virtualenv will be located in 
in `$HOME/.vep/aaa_venv`. For `bbb` it will be `$HOME/.vep/bbb_venv`. 

If you don't like `$HOME/.vep`, you can define the environment variable `$VEPDIR`. So 
for the project `aaa` the virtualenv will be located in `$VEPDIR/aaa`.

# Usage

To **create** new virtualenv with Python 3.8 in `$VEPDIR/myProject_venv`:

```bash
$ cd /path/to/myProject
$ vep init python3
```

The `python3` here is the exactly the interpreter will be used for that virtualenv. If you have 
more than one Python version, you can use something like

```bash
$ vep init python39
```
```bash
$ vep init /usr/local/opt/python@3.8/bin/python
```

	
To **remove** old and **create** new virtualenv:

```bash
$ cd /path/to/myProject
$ vep reinit python3
```

To **run** a **python script** inside `myProject_venv` environment: 
```bash 		
cd /path/to/myProject
pyvnv run python ./myProgram.py
```

To **run** a **bash subshell** inside `myProject_venv` environment:
```bash	
cd /path/to/myProject
pyvnv shell
```