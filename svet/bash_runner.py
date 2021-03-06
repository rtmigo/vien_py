import subprocess
from subprocess import Popen, TimeoutExpired, CalledProcessError, CompletedProcess


def run_as_bash_script_old(script: str, timeout: float = None, stdin=None) -> subprocess.CompletedProcess:
    """Runs the provided string as a .sh script.
    We need it as a separate function to test it well on different OSes.
    """

    # we need executable='/bin/bash' for Ubuntu, it will run /bin/sh otherwise.
    # In MacOS 10.13 it seems to be optional
    return subprocess.run(script, shell=True, executable='/bin/bash', timeout=timeout, stdin=None)

def run_as_bash_script(script: str, timeout: float = None, stdin=None, check:bool=False) -> subprocess.CompletedProcess:

    with Popen(args=script, shell=True) as process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise TimeoutExpired(process.args, timeout, output=stdout,
                                 stderr=stderr)
        except:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() as .__exit__ does that for us.
            raise
        retcode = process.poll()
        if check and retcode:
            raise CalledProcessError(retcode, process.args,
                                     output=stdout, stderr=stderr)
    return CompletedProcess(process.args, retcode, stdout, stderr)

