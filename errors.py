class SubprocessError(Exception):
    """
    Exception object that contains information about an error that occurred
    when running a command line command with a subprocess.
    """
    def __init__(self, cmd, return_code, stdout, stderr, *args):
        msg = 'Got non-zero exit code ({1}) from command "{0}": {2}'
        if stderr.strip():
            err_msg = stderr
        else:
            err_msg = stdout
        msg = msg.format(cmd[0], return_code, err_msg)
        self.cmd = cmd
        self.cmd_return_code = return_code
        self.cmd_stdout = stdout
        self.cmd_stderr = stderr
        super(SubprocessError, self).__init__(msg, *args)


class FfmpegValidationError(Exception):
    """
    Exception object that is raised when `ffmpeg` output does not validate.
    """
    pass

class FfmpegIncorrectDurationError(FfmpegValidationError):
    """
    Exception object that is raised when `ffmpeg` output has an expected duration
    """
    def __init__(self, filepath, target_duration, actual_duration, *args):
        self.filepath = filepath
        self.target_duration = target_duration
        self.actual_duration = actual_duration
        msg = "Output at {} was expected to be duration {} seconds, but got {} seconds"
        msg = msg.format(filepath, target_duration, actual_duration)
        super(FfmpegIncorrectDurationError, self).__init__( msg, *args)
