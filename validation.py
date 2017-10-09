import os.path
import sox

from errors import FfmpegValidationError, FfmpegIncorrectDurationError


def validate_audio(audio_filepath, audio_info):
    """
    Take audio file and sanity check basic info.

        Sample output from sox:
            {
                'bitrate': 16,
                'channels': 2,
                'duration': 9.999501,
                'encoding': 'FLAC',
                'num_samples': 440978,
                'sample_rate': 44100.0,
                'silent': False
            }

    Args:
        audio_filepath:   Path to output audio
                          (Type: str)

        audio_info:       Audio info dict
                          (Type: dict[str, *])

    Returns:
        check_passed:  True if sanity check passed
                       (Type: bool)
    """
    if not os.path.exists(audio_filepath):
        error_msg = 'Output file {} does not exist.'.format(audio_filepath)
        raise FfmpegValidationError(error_msg)

    sox_info = sox.file_info.info(audio_filepath)

    # If duration specifically doesn't match, catch that separately so we can
    # retry with a different duration
    target_duration = audio_info['duration']
    actual_duration = sox_info['num_samples'] / audio_info['sample_rate']
    if target_duration != actual_duration:
        raise FfmpegIncorrectDurationError(audio_filepath, target_duration,
                                           actual_duration)
    for k, v in audio_info.items():
        output_v = sox_info[k]
        if v != output_v:
            error_msg = 'Output audio {} should have {} = {}, but got {}.'.format(audio_filepath, k, v, output_v)
            raise FfmpegValidationError(error_msg)
