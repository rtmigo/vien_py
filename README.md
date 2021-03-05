# [vep](https://github.com/rtmigo/vep)

[![Generic badge](https://img.shields.io/badge/ready_for_use-no-red.svg)](#)

Command-line shortcuts for Python virtual environments.

VEP helps managing virtual environments located in `$VEPDIR`. 

For a Python project `/path/to/myProject/` the virtualenv will be located in 
in `$VEPDIR/myProject_venv/`

To **create** new virtualenv with Python 3.8 in `$VEPDIR/myProject_venv`:

```bash
$ cd /path/to/myProject
$ vep init 3.8
```
	
To **remove** old and **create** new virtualenv:

```bash
$ cd /path/to/myProject
$ vep reinit 3.8
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