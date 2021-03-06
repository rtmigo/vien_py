import subprocess
from typing import *


def run_as_bash_script(commands: Union[List[str], str]):
    bashLines = [
        "#!/bin/bash"
        # "set -e",  # fail on first error
    ]

    if isinstance(commands, str):
        commands = [commands]

    bashLines.extend(commands)

    # we need executable='/bin/bash' for Ubuntu, it will run /bin/sh otherwise.
    # In MacOS 10.13 it seems to be optional
    return subprocess.call("\n".join(bashLines), shell=True, executable='/bin/bash')

