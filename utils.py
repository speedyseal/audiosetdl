import os
import subprocess as sp
import re

URL_PATTERN = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)')


class SubprocessError(Exception):
    """
    Exception object that contains information about an error that occurred
    when running a command line command with a subprocess.
    """
    def __init__(self, cmd, return_code, stdout, stderr, *args):
        msg = 'Got non-zero exit code ({1}) from command "{0}": {2}'
        msg = msg.format(cmd[0], return_code, stderr)
        self.cmd = cmd
        self.cmd_return_code = return_code
        self.cmd_stdout = stdout
        self.cmd_stderr = stderr
        super(SubprocessError, self).__init__(msg, *args)


def run_command(cmd, **kwargs):
    """
    Run a command line command

    Args:
        cmd:       List of strings used in the command
                   (Type: list[str])

        **kwargs:  Keyword arguments to be passed to subprocess.Popen()

    Returns:
        stdout:       stdout string produced by running command
                      (Type: str)

        stderr:       stderr string produced by running command
                      (Type: str)

        return_code:  Exit/return code from running command
                      (Type: int)
    """
    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, **kwargs)
    stdout, stderr = proc.communicate()

    return_code = proc.returncode

    if return_code != 0:
        raise SubprocessError(cmd, return_code, stdout.decode(), stderr.decode())

    return stdout, stderr, return_code


def is_url(path):
    """
    Returns True if the given path is a URL.

    Assumes a proper URL specifies the HTTP/HTTPS protocol

    Args:
        path:  Path to file
               (Type: str)

    Returns:
        is_url:  True, if path is a URL
                 (Type: bool)
    """
    return bool(URL_PATTERN.match(path))


def get_filename(path):
    """
    Gets the filename from a path (or URL)

    Args:
        path:  Path or URL
               (Type: str)

    Returns:
        filename:  Filename
                   (Type: str)
    """
    return os.path.basename(path).split('?')[0]


def get_subset_name(subset_path):
    """
    Gets the name of a subset of the subset file at the given path.

    The subset name is simply taken the filename without the extension.

    Args:
        subset_path:  Path to subset segments file
                      (Type: str)

    Returns:
        subset_name:  Name of subset
                      (Type: str)
    """
    subset_filename = get_filename(subset_path)
    subset_name, ext = os.path.splitext(subset_filename)
    if ext[1:].isdigit():
        subset_name, file_num = os.path.splitext(subset_name)

    return subset_name