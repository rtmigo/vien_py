# SPDX-FileCopyrightText: (c) 2021-2022 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import os
import time
from pathlib import Path
from subprocess import Popen, TimeoutExpired, CalledProcessError, \
    CompletedProcess, PIPE
from tempfile import NamedTemporaryFile
from typing import Optional, List, Dict


def _run_with_input_delay(*popenargs,
                          input_delay: float = None,
                          input: Optional[bytes] = None,
                          # stdin: Optional[bytes] = None,
                          timeout: float = None,
                          check: bool = False,
                          capture_output: bool = False,
                          **kwargs):
    """Basically the same as subprocess.run, but accepts input_delay
    parameter."""

    # This is almost an exact copy of subprocess.run (as of 2021-03-06).
    # SPDX-FileCopyrightText: 2003-2005 Peter Astrand <astrand@lysator.liu.se>
    # https://github.com/python/cpython/blob/master/Lib/subprocess.py

    # START of insert from another portion of subprocess.py
    try:
        import msvcrt
        import _winapi
        _mswindows = True
    except ModuleNotFoundError:
        _mswindows = False
    # END of insert

    if input is not None:
        if kwargs.get('stdin') is not None:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = PIPE

    if capture_output:
        if kwargs.get('stdout') is not None or kwargs.get('stderr') is not None:
            raise ValueError('stdout and stderr arguments may not be used '
                             'with capture_output.')
        kwargs['stdout'] = PIPE
        kwargs['stderr'] = PIPE

    with Popen(*popenargs, **kwargs) as process:
        try:
            # START of modified code
            if input is not None and input_delay:
                time.sleep(input_delay)
            # END of modified code

            stdout, stderr = process.communicate(input, timeout=timeout)
        except TimeoutExpired as exc:
            process.kill()
            if _mswindows:
                # Windows accumulates the output in a single blocking
                # read() call run on child threads, with the timeout
                # being done in a join() on those threads.  communicate()
                # _after_ kill() is required to collect that and add it
                # to the exception.
                exc.stdout, exc.stderr = process.communicate()
            else:
                # POSIX _communicate already populated the output so
                # far into the TimeoutExpired exception.
                process.wait()
            raise
        except:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() as .__exit__ does that for us.
            raise

        exit_code = process.poll()

        # START of modified code
        if exit_code is None:
            raise RuntimeError("The process was not terminated.")
        # END of modified code

        if check and exit_code:
            raise CalledProcessError(exit_code, process.args,
                                     output=stdout, stderr=stderr)

    return CompletedProcess(process.args, exit_code, stdout, stderr)


def start_bash_shell(init_commands: List[str],
                     input: Optional[str] = None,
                     input_delay: Optional[float] = None,
                     env: Optional[Dict] = None) -> CompletedProcess:
    ubuntu_bashrc_path = Path(os.path.expanduser("~/.bashrc")).absolute()

    if ubuntu_bashrc_path.exists():
        # Ubuntu
        with NamedTemporaryFile('r', suffix=".rc") as tdf:
            init_commands = [f"source {ubuntu_bashrc_path}"] + init_commands

            # creating temporary init script (like bash.rc)
            temp_bash_rc = Path(tdf.name)
            temp_bash_rc.write_text('\n'.join(init_commands))

            return _run_with_input_delay(
                ["/bin/bash", "--rcfile", str(temp_bash_rc), "-i"],
                executable=None,
                input=input.encode() if input else None,
                input_delay=input_delay,
                env=env)
    else:
        # MacOS
        return _run_with_input_delay(
            "\n".join(init_commands),
            executable="/bin/bash",
            input=input.encode() if input else None,
            input_delay=input_delay,
            env=env)
