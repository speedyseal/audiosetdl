import sox

from errors import FfmpegValidationError


def sanity_check_audio(audio_filepath, audio_info):
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
        audio_filepath:  Path to output audio
                         (Type: str)

        audio_info:      Audio info dict
                         (Type: dict[str, *])

    Returns:
        check_passed:  True if sanity check passed
                       (Type: bool)
    """

    sox_info = sox.file_info.info(audio_filepath)
    return all([v == sox_info[k] for k, v in audio_info.items()])


def validate_audio(audio_filepath, audio_info):
    """
    Validate output audio from `ffmpeg`

    Args:
        audio_filepath:  Path to output audio
                         (Type: str)

        audio_info:      Audio info dict
                         (Type: dict[str, *])
    """
    if not sanity_check_audio(audio_filepath, audio_info):
        error_msg = 'Audio {} is corrupted.'.format(audio_filepath)
        raise FfmpegValidationError(error_msg)