import json
import os.path
import sox

from errors import FfmpegValidationError, FfmpegIncorrectDurationError
from utils import run_command

import logging
import logging.handlers
LOGGER = logging.getLogger('audiosetdl')
LOGGER.setLevel(logging.DEBUG)

TOL = 0.7   # allow 0.7s variation in length

def ffprobe(ffprobe_path, filepath):
    """
    Run ffprobe to analyse audio or video file

    Args:
        ffprobe_path:  Path to ffprobe executable
                       (Type: str)

        filepath:      Path to audio or video file to analyse
                       (Type: str)

    Returns:
        output:  JSON object returned by ffprobe
                 (Type: JSON comptiable dict)
    """
    cmd_format = '{} -v quiet -print_format json -show_format -show_streams {}'
    cmd = cmd_format.format(ffprobe_path, filepath).split()
    stdout, stderr, retcode = run_command(cmd)
    return json.loads(stdout)


def validate_audio(audio_filepath, audio_info, end_past_video_end=False):
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
        #if not(end_past_video_end and actual_duration < target_duration):
        if actual_duration < (target_duration - TOL) or actual_duration > (target_duration+TOL):
            raise FfmpegIncorrectDurationError(audio_filepath, target_duration,
                                               actual_duration)
    for k, v in audio_info.items():
        if k == 'duration': #and (end_past_video_end and actual_duration < target_duration):
            continue

        output_v = sox_info[k]

        try:
            v = float(v)
        except ValueError:
            #LOGGER.warning("Could not convert audio info value {} for key {}".format(v, k))
            pass
        try:
            output_v = float(output_v)
        except ValueError:
            #LOGGER.warning("Could not convert sox info value {} for key {}".format(output_v, k))
            pass

        if v != output_v:
            error_msg = 'Output audio {} should have {} = {}, but got {}.'.format(audio_filepath, k, v, output_v)
            raise FfmpegValidationError(error_msg)


def validate_video(video_filepath, ffprobe_path, video_info, end_past_video_end=False):
    """
    Take video file and sanity check basic info.

    Args:
        video_filepath:  Path to output video file
                         (Type: str)

        ffprobe_path:    Path to ffprobe executable
                         (Type: str)

        video_info:      Video info dictionary
                         (Type: str)
    """
    ffprobe_info = ffprobe(ffprobe_path, video_filepath)
    if not ffprobe_info:
        error_msg = 'Could not analyse {} with ffprobe'
        raise FfmpegValidationError(error_msg.format(video_filepath))

    # Get the video stream data
    if not ffprobe_info.get('streams'):
        error_msg = '{} has no video streams!'
        raise FfmpegValidationError(error_msg.format(video_filepath))
    ffprobe_info = next(stream for stream in ffprobe_info['streams'] if stream['codec_type'] == 'video')

    # If duration specifically doesn't match, catch that separately so we can
    # retry with a different duration
    target_duration = video_info['duration']
    try:
        actual_fr_ratio = ffprobe_info.get('r_frame_rate',
                                           ffprobe_info['avg_frame_rate'])
        fr_num, fr_den = actual_fr_ratio.split('/')
        actual_framerate = float(fr_num) / float(fr_den)
    except KeyError:
        error_msg = 'Could not get frame rate from {}'
        raise FfmpegValidationError(error_msg.format(video_filepath))
    actual_duration = float(ffprobe_info['nb_frames']) / actual_framerate
    if target_duration != actual_duration:
        #if not(end_past_video_end and actual_duration < (target_duration-TOL)):
        if actual_duration < (target_duration - TOL) or actual_duration > (target_duration+TOL):
            raise FfmpegIncorrectDurationError(video_filepath, target_duration,
                                               actual_duration)

    for k, v in video_info.items():
        if k == 'duration': # and (end_past_video_end and actual_duration < target_duration):
            continue

        output_v = ffprobe_info[k]

        # Convert numeric types to float, since we may get strings from ffprobe
        try:
            v = float(v)
        except ValueError:
            #LOGGER.warning("Could not convert video info value {} for key {}".format(v, k))
            pass
        try:
            output_v = float(output_v)
        except ValueError:
            #LOGGER.warning("Could not convert ffprobe value {} for key {}".format(output_v, k))
            pass

        # if duration, and within tolerance, then short circuit the v!=output_v test
        if v != output_v:
            error_msg = 'Output video {} should have {} = {}, but got {}.'.format(video_filepath, k, v, output_v)
            raise FfmpegValidationError(error_msg)

