#!/usr/bin/env python
'''
Downloads Google's AudioSet dataset locally
'''
from __future__ import unicode_literals
import argparse
import csv
import logging, logging.handlers
import multiprocessing as mp
import os
import traceback as tb
import urllib2
import multiprocessing_logging
import youtube_dl
from youtube_dl.utils import YoutubeDLError, MaxDownloadsReached, \
                             DownloadError, PostProcessingError, \
                             UnavailableVideoError


LOGGER = logging.getLogger('audiosetdl')
LOGGER.setLevel(logging.DEBUG)


def parse_arguments():
    '''
    Parse arguments from the command line


    Returns:
        args:  Argument dictionary
               (Type: dict[str, str])
    '''
    parser = argparse.ArgumentParser(description='Download AudioSet data locally')

    parser.add_argument('-f',
                        '--ffmpeg',
                        dest='ffmpeg_path',
                        action='store',
                        type=str,
                        default='./bin/miniconda/bin/ffmpeg',
                        help='Path to ffmpeg executable')

    parser.add_argument('-e',
                        '--eval',
                        dest='eval_segments_url',
                        action='store',
                        type=str,
                        default='http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/eval_segments.csv',
                        help='Path to evaluation segments file')

    parser.add_argument('-b',
                        '--balanced-train',
                        dest='balanced_train_segments_url',
                        action='store',
                        type=str,
                        default='http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/balanced_train_segments.csv',
                        help='Path to balanced train segments file')

    parser.add_argument('-u',
                        '--unbalanced-train',
                        dest='unbalanced_train_segments_url',
                        action='store',
                        type=str,
                        default='http://storage.googleapis.com/us_audioset/youtube_corpus/v1/csv/unbalanced_train_segments.csv',
                        help='Path to unbalanced train segments file')

    parser.add_argument('-n',
                        '--num-workers',
                        dest='num_workers',
                        action='store',
                        type=int,
                        default=4,
                        help='Number of multiprocessing workers used to download videos')

    parser.add_argument('-nl',
                        '--no-logging',
                        dest='disable_logging',
                        action='store_true',
                        default=False,
                        help='Disables logging if flag enabled')

    parser.add_argument('-v',
                        '--verbose',
                        dest='verbose',
                        action='store_true',
                        default=False,
                        help='Prints verbose info to stdout')

    parser.add_argument('data_dir',
                        action='store',
                        type=str,
                        help='Path to directory where AudioSet data will be stored')


    return vars(parser.parse_args())


def download_yt_video(ytid, ts_start, output_dir, ffmpeg_path):
    """
    Download a Youtube video


    The output filename is of the format:
        <YouTube ID>_<start time in ms>_<end time in ms>.<extension>

    Args:
        ytid:         Youtube ID string
                      (Type: str)

        ts_start:     Segment start time (in seconds)
                      (Type: float)

        output_dir:   Output directory where video will be saved
                      (Type: str)

        ffmpeg_path:  Path to ffmpeg executable
                      (Type: str)
    """
    # Compute some things from the segment boundaries
    ts_end = ts_start + 10
    tms_start, tms_end = int(ts_start * 1000), int(ts_end * 1000)

    # Make the output format and video URL
    # Output format is in the format:
    #   <YouTube ID>_<start time in ms>_<end time in ms>.<extension>
    filename_fmt = '{}_{}_{}.%(ext)s'.format(ytid, tms_start, tms_end)
    output_fmt = os.path.join(output_dir, filename_fmt)
    video_url = 'https://www.youtube.com/watch?v={}'.format(ytid)

    # List of opts: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L137
    ydl_opts = {
        'external_downloader': 'ffmpeg',
        'external_downloader_args': ['-ss', str(ts_start), '-t', '10'],
        'prefer_free_formats': True,
        'outtmpl': output_fmt,
        'prefer_ffmpeg': True,
        'nooverwrites': True, # Only applies to metadata
        'restrictfilenames': True,
        #'skip_download': True, # NOTE: FOR DEBUG
    }

    # Download video
    # NOTE: Automatically handles existing files: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L1855
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        retcode = ydl.download([video_url])

    # TODO: Figure out why mkv's and webm files are not 10 seconds

    ts_end = ts_start + 10
    if retcode == 0:
        LOGGER.info('Downloaded video {} ({} - {})'.format(ytid, ts_start, ts_end))
    else:
        LOGGER.info('Did not download video {} ({} - {})'.format(ytid, ts_start, ts_end))


def segment_mp_worker(ytid, ts_start, video_dir, ffmpeg_path):
    """

        ytid:         Youtube ID string
                      (Type: str)

        ts_start:     Segment start time (in seconds)
                      (Type: float)

        video_dir:    Directory where videos will be saved
                      (Type: str)

        ffmpeg_path:  Path to ffmpeg executable
                      (Type: str)
    """
    ts_end = ts_start + 10
    LOGGER.info('Attempting to download video {} ({} - {})'.format(ytid, ts_start, ts_end))

    # Download the video
    try:
        download_yt_video(ytid, ts_start, video_dir, ffmpeg_path)
    except MaxDownloadsReached as e:
        err_msg = 'Maximum downloads reached: {}'.format(e)
        LOGGER.error(err_msg)
        sys.exit(err_msg.format(e))
    except UnavailableVideoError as e:
        err_msg = 'Video {} was unavailable: {}'.format(ytid, e)
        LOGGER.error(err_msg)
    except DownloadError as e:
        err_msg = 'Error downloading video {}: {}'.format(ytid, e)
        LOGGER.error(err_msg)
    except PostProcessingError as e:
        err_msg = 'Error while post-processing video {}: {}'.format(ytid, e)
        LOGGER.error(err_msg)
        sys.exit(err_msg)
    except YoutubeDLError:
        err_msg = 'YoutubeDL error while processing video {}: {}'.format(ytid, e)
        LOGGER.error(err_msg)
        sys.exit(err_msg)
    except Exception as e:
        err_msg = 'Error while processing video {}: {}; {}'.format(ytid, e, tb.format_exc())
        LOGGER.error(err_msg)
        raise


def download_subset_files(subset_url, data_dir, ffmpeg_path, num_workers):
    """
    Download subset segment file and videos

    Args:
        subset_url:   URL to subset segments file
                      (Type: str)

        data_dir:     Directory where dataset files will be saved
                      (Type: str)

        ffmpeg_path:  Path to ffmpeg executable
                      (Type: str)

        num_workers:  Number of multiprocessing workers used to download videos
                      (Type: int)
    """

    # Get filename of the subset file
    subset_filename = subset_url.split('/')[-1].split('?')[0]
    subset_path = os.path.join(data_dir, subset_filename)

    # Derive video directory name
    video_dir = os.path.join(data_dir, 'data', os.path.splitext(subset_filename)[0])
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)

    # Open subset file as a CSV
    if not os.path.exists(subset_path):
        with open(subset_path, 'wb') as f:
            subset_data = urllib2.urlopen(subset_url).read()
            f.write(subset_data)

    with open(subset_path, 'rb') as f:
        subset_data = csv.reader(f)

        # Set up multiprocessing pool
        pool = mp.Pool(num_workers)
        try:
            for row_idx, row in enumerate(subset_data):
                # Skip the 3 line header
                if row_idx < 3:
                    continue
                worker_args = [row[0], float(row[1]), video_dir, ffmpeg_path]
                pool.apply_async(segment_mp_worker, worker_args)

        except csv.Error as e:
            err_msg = 'Encountered error in {} at line {}: {}'
            LOGGER.error(err_msg)
            sys.exit(err_msg.format(filename, reader.line_num, e))
        finally:
            pool.close()
            pool.join()


def init_file_logger():
    """
    Initializes logging to a file.

    Saves log to "audiosetdl.log" in the current directory, and rotates them
    after they reach 1MiB.
    """
    # Set up file handler
    filename = 'audiosetdl.log'
    handler = logging.handlers.RotatingFileHandler(filename, maxBytes=2**20)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)


def init_stdout_logger(verbose):
    """
    Initializes logging to stdout

    Args:
        verbose:  If true, prints verbose information to stdout
                  (Type: bool)
    """
    # Log to stdout also
    stream_handler = logging.StreamHandler()
    if verbose:
        stream_handler.setLevel(logging.DEBUG)
    else:
        stream_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    LOGGER.addHandler(stream_handler)


def download_audioset(data_dir, ffmpeg_path, eval_segments_url,
                      balanced_train_segments_url, unbalanced_train_segments_url,
                      disable_logging, verbose, num_workers):
    """
    Download AudioSet files

    Args:
        data_dir:                       Directory where dataset files will
                                        be saved
                                        (Type: str)

        ffmpeg_path:                    Path to ffmpeg executable
                                        (Type: str)

        eval_segments_url:              Path to evaluation segments file
                                        (Type: str)

        balanced_train_segments_url:    Path to balanced train segments file
                                        (Type: str)

        unbalanced_train_segments_url:  Path to unbalanced train segments file
                                        (Type: str)

        disable_logging:                Disables logging to a file if True
                                        (Type: bool)

        verbose:                        Prints verbose information to stdout
                                        if True
                                        (Type: bool)

        num_workers:                    Number of multiprocessing workers used
                                        to download videos
                                        (Type: int)
    """
    init_stdout_logger(verbose)
    if not disable_logging:
        init_file_logger()
    #multiprocessing_logging.install_mp_handler()
    LOGGER.debug('Initialized logging.')

    download_subset_files(eval_segments_url, data_dir, ffmpeg_path, num_workers)
    download_subset_files(balanced_train_segments_url, data_dir, ffmpeg_path, num_workers)
    download_subset_files(unbalanced_train_segments_url, data_dir, ffmpeg_path, num_workers)


if __name__ == '__main__':
    download_audioset(**parse_arguments())
