[![PyPI version shields.io](https://img.shields.io/pypi/v/vien.svg)](https://pypi.python.org/pypi/vien/)
[![Generic badge](https://img.shields.io/badge/OS-Linux%20|%20macOS-blue.svg)](#)
[![Generic badge](https://img.shields.io/badge/Python-3.7+-blue.svg)](#)

# [vien](https://github.com/rtmigo/vien_py#readme)

**VIEN** is a command-line tool for managing
[Python Virtual Environments](https://docs.python.org/3/library/venv.html).

It provides one-line shortcuts for:

- creating and deleting environments
- running commands inside environments
- switching between environments in bash shell

-----

Switching between projects should be simple. Creating environments for the
projects should be simple too.

Ideally it's a short command that I would type even half asleep.

Something like

``` bash
$ vien create 
$ vien shell
```

Not like

``` bash
$ python3 -m venv ./where/to/put/this/.venv
$ source /i/lost/that/.venv/bin/activate
```

<details>
  <summary>Ready-made solutions did not help.</summary><br/>

- [pipenv](https://pipenv.pypa.io/) kind of solved the problem, but brought new
  challenges unrelated to virtual environments
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/) name is easier
  to copy-paste than to type. And its commands are too

</details>

So there is the `vien`. A tool for a half asleep developer.

# Install

<details>
  <summary>Get a working Python ≥3.7, pip3 and venv.</summary><br/>

@ Ubuntu

``` bash
$ sudo apt install -y python3 python3-pip python3-venv
```

@ macOS

``` bash
$ brew install python3
```

Check it works

``` bash
$ python3 --version             # python shows its version
$ python3 -m venv --help        # venv shows help message
$ pip3 install --upgrade pip    # pip upgrades itself
```

----
</details>

Then:

``` bash
$ pip3 install vien
```

Make sure it installed:

``` bash
$ vien      # shows help
```

Upgrade it later:

``` bash
$ pip3 install vien --upgrade
```

# Use

### Example: interactive shell

``` bash
$ cd /path/to/myProject
$ vien create
$ vien shell
```

### Example: running commands

``` bash
$ cd /path/to/myProject
$ vien create
$ vien run pip install --upgrade pip
$ vien run pip install requests lxml
$ vien call main.py
```

# Commands

## create

`vien create` сreates a virtual environment that will correspond the current
working directory. The **working directory** in this case is assumed to be
your **project directory**. Subsequent calls to other `vien` commands in the
same directory will use the same virtual environment.

``` bash
$ cd /path/to/myProject
$ vien create 
```

By default `vien` will try to use `python3` as the interpreter for the virtual
environment.

If you have more than one Python version, you can provide an argument to point
to the proper interpreter.

``` bash
$ vien create /usr/local/opt/python@3.8/bin/python3
```

In many cases, a shorter command will also work. If the needed interpreter can
be executed in the shell as `python3.8`, you can try

``` bash
$ vien create python3.8
```

## shell

`vien shell` starts interactive bash session in the virtual environment.

``` bash	
$ cd /path/to/myProject
$ vien shell

(myProject)$ _
```

Now you are inside the virtual environment.

``` bash	
(myProject)$ which python3             # now we are using separate copy of Python
(myProject)$ echo $PATH                # everything is slightly different

(myProject)$ pip3 install requests     # installs packages into virtual environment
(myProject)$ python3 use_requests.py   # runs inside the virtual environment
```

Get out of the virtual environment:

``` bash
(myProject)$ exit

$ _
```

Now you're back.

With shell pipes, you can specify what the shell should execute right in the 
command line.

``` bash
$ echo 'which python3 && echo $PATH' | vien shell
```

## run

`vien run COMMAND` runs a shell command in the virtual environment.

``` bash 		
$ cd /path/to/myProject
$ vien run python3 use_requests.py arg1 arg2  # runs script in virtual environment
$ vien run pip3 install requests              # installs packages into virtual environment
```

<details>
  <summary>is an equivalent to</summary><br/>

``` bash 		
$ cd /path/to/myProject

$ source /path/to/the/venv/bin/activate
$ python3 use_requests.py arg1 arg2
$ /path/to/the/venv/bin/deactivate

$ source /path/to/the/venv/bin/activate
$ pip3 install requests
$ /path/to/the/venv/bin/deactivate
```

</details>

## call

`vien call PYFILE` executes a `.py` script in the virtual environment.

``` bash 		
$ cd /path/to/myProject
$ vien call main.py
```

The optional `-p` parameter allows you to specify the project directory
**relative** to the parent directory of the **file** being run.

``` bash 		
$ cd any/where  # working dir is irrelevant

# absolute (using venv for /abc/myProject):
$ vien call -p /abc/myProject /abc/myProject/main.py

# relative (using venv for /abc/myProject):
$ vien call -p . /abc/myProject/main.py

# error (there is no venv for any/where)
$ vien call /abc/myProject/main.py
```

This parameter makes things like [shebang](#Shebang) possible.

## delete

`vien delete` deletes the virtual environment.

``` bash
$ cd /path/to/myProject
$ vien delete 
```

## recreate

`vien recreate` old and creates new virtual environment.

If you decided to start from scratch:

``` bash
$ cd /path/to/myProject
$ vien recreate 
```

If you decided to change the Python version:

``` bash
$ cd /path/to/myProject
$ vien recreate /usr/local/opt/python@3.10/bin/python3
```

# Virtual environments location

By default, `vien` places virtual environments in the `$HOME/.vien` directory.

|project dir|virtual environment dir|
|-----|----|
|`/abc/thisProject`|`$HOME/.vien/thisProject_venv`|
|`/abc/otherProject`|`$HOME/.vien/otherProject_venv`|
|`/moved/to/otherProject`|`$HOME/.vien/otherProject_venv`|

Only the local name of the project directory matters.

If you're not happy with the default, you can set the environment
variable `VIENDIR`:

``` bash
$ export VIENDIR="/x/y/z"
```

So for the project `aaa` the virtual environment will be located
in `/x/y/z/aaa_venv`.

The `_venv` suffix tells the utility that this directory can be safely removed.

# Shell prompt

By default the `vien shell` adds a prefix to
the [`$PS1`](https://wiki.archlinux.org/index.php/Bash/Prompt_customization)
bash prompt.

``` bash
user@host$ cd /abc/myProject
user@host$ vien shell

(myProject)user@host$ _
```

So you can see, which virtual environment you're using.

If you customized your `PS1`, it may not work as expected.

``` bash
personalized:prompt> cd /abc/myProject
personalized:prompt> vien shell

(myProject)user@host$ _
```

It can be fixed by providing `PS1` variable to `vien` like that:

``` bash
personalized:prompt> cd /abc/myProject
personalized:prompt> PS1=$PS1 vien shell

(myProject)personalized:prompt> _
```

To avoid doing this each time, `export` your `PS1` to make it available for
subprocesses.

# Shebang

On POSIX systems, you can make a `.py` file executable, with `vien` executing it
inside a virtual environment.

Insert the shebang line to the top of the file you want to run. The value of the
shebang depends on the location of the file relative to the project directory.

File                            | Shebang line
--------------------------------|--------------------------------
`myProject/runme.py`            | `#!/usr/bin/env vien call -p .`
`myProject/pkg/runme.py`        | `#!/usr/bin/env vien call -p ..`
`myProject/pkg/subpkg/runme.py` | `#!/usr/bin/env vien call -p ../..`

After inserting the shebang, make the file executable:

``` bash
$ chmod +x runme.py  
```

Now you can run the `runme.py` directly from command line. This will use the
virtual environment associated with the `myProject`. The working directory can
be anything.

``` bash
# runs the runme.py in virtual environment for myProject

$ cd anywhere/somewhere
$ /abc/myProject/pkg/main.py   
```
