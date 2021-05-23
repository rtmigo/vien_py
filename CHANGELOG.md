# 4.4

- `call` is now faster as it launches Python directly without spawning an extra 
  shell process

# 4.3

- A much shorter help message now appears when running `vien` without parameters
- Fixed: `call` printed debug message to stdout

# 4.2

- Trying to `call` a non-existent file now prints a short error message 
  instead of an exception
- A message about a nonexistent environment displays a hint on how to create it  

# 4.1

- Fixed: `$VIENDIR` did not change the storage directory of the virtual
  environments

# 4.0

- "call" command added
- New versioning scheme
- Fixed: the 'run' command could be run when the virtual environment does not
  exist

# 0.3.7

- Fixed: "run" and "shell" commands returned exit code 0 regardless of the exit
  code of the child process 