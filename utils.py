import os
import re
import subprocess as sp

from errors import SubprocessError

URL_PATTERN = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)')
HTTP_ERR_PATTERN = re.compile(r'Server returned (4|5)(X|[0-9])(X|[0-9])')


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
    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True, **kwargs)
    stdout, stderr = proc.communicate()

    return_code = proc.returncode

    if return_code != 0:
        raise SubprocessError(cmd, return_code, stdout, stderr)

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


def get_media_filename(ytid, ts_start, ts_end):
    """
    Get the filename (without extension) for a media file (audio or video) for a YouTube video segment

    Args:
        ytid:      YouTube ID of a video
                   (Type: str)

        ts_start:  Segment start time (in seconds)
                   (Type: float or int)

        ts_end:    Segment end time (in seconds)
                   (Type: float or int)

    Returns:
        media_filename:  Filename (without extension) for segment media file
                         (Type: str)
    """
    tms_start, tms_end = int(ts_start * 1000), int(ts_end * 1000)
    return '{}_{}_{}'.format(ytid, tms_start, tms_end)


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