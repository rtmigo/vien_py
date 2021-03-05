# [vep](https://github.com/rtmigo/vep#readme)

[![Generic badge](https://img.shields.io/badge/ready_for_use-no-red.svg)](#)
[![Actions Status](https://github.com/rtmigo/vep/workflows/CI/badge.svg?branch=master)](https://github.com/rtmigo/vep/actions)
[![Generic badge](https://img.shields.io/badge/CI_OS-MacOS,_Ubuntu-blue.svg)](#)
[![Generic badge](https://img.shields.io/badge/CI_Python-3.7--3.9-blue.svg)](#)

Command-line shortcuts for managing Python virtualenvs.

# Why

Switching between different projects in Python should be simple. A short command 
that I would type even half asleep.

Not something like
```base
# python3 -m venv ./i/have/no/idea/where/to/put/this/.venv
$ source /where/is/that/damn/directory/.venv/bin/activate
```

But something like
```base
$ cd /abc/myproject
$ vep init python39
$ vep shell
```

As a ready-made solution to the problem, I tried [pipenv](https://pipenv.pypa.io/). It kind of 
solved the problem, but also brought new challenges that dwarfed the old ones. I didn't sign 
up for this.

So I made `vep`. A stupidly simple tool for a half asleep developer.

# What is does

`vep` offers a simple rule of where to place the virtualenv.

|project dir|virtualenv dir|
|-----|----|
|`/abc/thisProject`|`$HOME/.vepvep/thisProject_venv`|
|`/abc/otherProject`|`$HOME/.vepvep/otherProject_venv`|
|`/moved/to/otherProject`|`$HOME/.vepvep/otherProject_venv`|

So only the local name of the project directory matters. And all the virtualenvs 
are in `$HOME/.vepvep`. Until you [change this dir](#vepdir).



# Usage

### Create a new virtualenv

```bash
$ cd /path/to/myProject
$ vep init python3
```

The `python3` here is the exactly the interpreter will be used for that virtualenv. If you have 
more than one Python version, just point to the proper binary the way you execute it:

```bash
$ vep init python3.9
```
```bash
$ vep init /usr/local/opt/python@3.8/bin/python
```

	
### Remove old and create new virtualenv

```bash
$ cd /path/to/myProject
$ vep reinit python3
```

### Run a python script inside the virtualenv 
```bash 		
$ cd /path/to/myProject
$ vep run python ./myProgram.py
```

### Run a bash subshell inside the virtualenv 
```bash	
$ cd /path/to/myProject
$ vep shell
```

# $VEPDIR

You can set the directory where `vep` places the virtualenvs. By default, it's `$HOME/.vepvep`. If you're not happy with this, you can define the environment variable `VEPDIR`:
```bash
$ export VEPDIR="/x/y/z"
```
So for the project `aaa` the virtualenv will be located in `/x/y/z/aaa_venv`.

The `_venv` suffix tells the utility that this directory can be safely removed.