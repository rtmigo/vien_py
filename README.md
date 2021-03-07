# [vien](https://github.com/rtmigo/vien#readme)
[![Generic badge](https://img.shields.io/badge/ready_for_use-no-red.svg)](#)
[![PyPI version shields.io](https://img.shields.io/pypi/v/vien.svg)](https://pypi.python.org/pypi/vien/)
[![Actions Status](https://github.com/rtmigo/vien/workflows/CI/badge.svg?branch=master)](https://github.com/rtmigo/vien/actions)
[![Generic badge](https://img.shields.io/badge/CI_OS-MacOS,_Ubuntu-blue.svg)](#)
[![Generic badge](https://img.shields.io/badge/CI_Python-3.7--3.9-blue.svg)](#)

**VIEN** is a command-line tool for managing [Python Virtual Environments](https://docs.python.org/3/library/venv.html) in bash.

It provides one-line shortcuts for:
- creating and deleting environments
- running commands inside environments
- switching between environments in bash shell
    

-----

Switching between projects should be simple. Creating environments for the projects should be simple too.

Ideally it's a short command that I would type even half asleep.

Something like
```base
$ vien create 
$ vien shell
```

And not like
```base
$ python3 -m venv ./where/to/put/this/.venv
$ source /i/lost/that/.venv/bin/activate
```


<details>
  <summary>Ready-made solutions did not help.</summary><br/>


- [pipenv](https://pipenv.pypa.io/) kind of solved the problem, but brought new challenges unrelated to virtualenvs
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) is a package whose name is easier to copy-paste than to type

</details>

So there is the `vien`. A tool for a half asleep developer.


# Install

<details>
  <summary>Get a working Python ≥3.7, pip3 and venv.</summary><br/>

@ Ubuntu
```bash
$ sudo apt install -y python3 python3-pip python3-venv
```

@ macOS
```bash
$ brew install python3
```
Check it works
```bash
$ python3 --version             # python shows its version
$ pip3 install --upgrade pip    # pip upgrades itself
$ python3 -m venv --help        # venv shows help message
```


----
</details>
  
Then:

```bash
$ pip3 install vien
```

Make sure it installed:

```bash
$ vien      # shows help
```

Upgrade it later:
```bash
$ pip3 install vien --upgrade
```


# Use

## Create a virtual environment

```bash
$ cd /path/to/myProject
$ vien create 
```

By default `vien` will try to use `python3` as the interpreter for the virtual environment.

<details>
  <summary>If you have 
more than one Python version, provide one more argument.</summary><br/>
Point to the proper interpreter the way you execute it.

If you execute scripts like that

```bash
$ python3.8 /path/to/script.py
```

Create virtual environment like that:

```bash
$ vien create python3.8
```

Or provide full path to the interpreter:

```bash
$ vien create /usr/local/opt/python@3.8/bin/python3
```
</details>

## Dive into interactive bash
```bash	
$ cd /path/to/myProject
$ vien shell

(myProject)$ _
```

Now you are inside the virtual environment.

```bash	
(myProject)$ pip3 install requests     # installs packages into virtualenv 

(myProject)$ python3 use_requests.py   # runs in virtualenv

(myProject)$ which python3             # we are using separate copy of Python

(myProject)$ echo $PATH                # everything is slightly different
```

Get out of the virtualenv:

```bash
(myProject)$ exit

$ _
```

Now you're back.

## Run a script inside the virtual environment

It is `vien run <any bash command>`

```bash 		
$ cd /path/to/myProject
$ vien run python3 use_requests.py arg1 arg2  # runs in virtualenv
$ vien run pip3 install requests              # installs packages into virtualenv
```

<details>
  <summary>is an equivalent to</summary><br/>

```bash 		
$ cd /path/to/myProject

$ source /path/to/the/venv/bin/activate
$ python3 use_requests.py arg1 arg2
$ /path/to/the/venv/bin/deactivate

$ source /path/to/the/venv/bin/activate
$ pip3 install requests
$ /path/to/the/venv/bin/deactivate
```
</details>


# Where are the virtual environments

`vien` offers a simple rule of where to place the virtualenv.

|project dir|virtualenv dir|
|-----|----|
|`/abc/thisProject`|`$HOME/.vien/thisProject_venv`|
|`/abc/otherProject`|`$HOME/.vien/otherProject_venv`|
|`/moved/to/otherProject`|`$HOME/.vien/otherProject_venv`|

So only the local name of the project directory matters. And all the virtualenvs 
are in `$HOME/.vien`. 

You can set the directory where `vien` places the virtual environments. By default, it's `$HOME/.vien`. If you're not happy with this, you can define the environment variable `VIENDIR`:
```bash
$ export VIENDIR="/x/y/z"
```
So for the project `aaa` the virtual environment will be located in `/x/y/z/aaa_venv`.

The `_venv` suffix tells the utility that this directory can be safely removed.

# Other commands

### Delete virtual environment

```bash
$ cd /path/to/myProject
$ vien delete 
```

### Delete old and create new virtual environment

Useful, when you want to start from scratch.
```bash
$ cd /path/to/myProject
$ vien recreate 
```
Optionally point to the interpreter:
```bash
$ cd /path/to/myProject
$ vien recreate /path/to/bin/python3
```

# Shell prompt

By default the `vien shell` adds a prefix to the [`$PS1`](https://wiki.archlinux.org/index.php/Bash/Prompt_customization) 
bash prompt.
```bash
user@host$ cd /abc/myProject
user@host$ vien shell

(myProject)user@host$ _
```
So you can see, which virtual environment you're using.

If you customized your `PS1`, it may not work as expected.  

```bash
personalized:prompt> cd /abc/myProject
personalized:prompt> vien shell

(myProject)user@host$ _
```

It can be fixed by providing `PS1` variable to `vien` like that: 

```bash
personalized:prompt> cd /abc/myProject
personalized:prompt> PS1=$PS1 vien shell

(myProject)personalized:prompt> _
```

To avoid doing this each time, `export` your `PS1` to make it available for subprocesses.