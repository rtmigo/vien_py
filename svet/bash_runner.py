import subprocess
from typing import *


def run_as_bash_script(command: str) -> subprocess.CompletedProcess:
    # we need executable='/bin/bash' for Ubuntu, it will run /bin/sh otherwise.
    # In MacOS 10.13 it seems to be optional
    #return subprocess.call(command, shell=True, executable='/bin/bash')
    return subprocess.run(command, shell=True, executable='/bin/bash')


#def run_as_bash_script_and_communicate(command: str):
 #   return subprocess.(command, shell=True, executable='/bin/bash')

