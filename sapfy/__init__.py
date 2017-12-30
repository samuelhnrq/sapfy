# pylint: disable=W0603
import logging as l
import wave as wav
import time
from queue import Queue, Empty
from threading import Event, Lock
from concurrent.futures import ThreadPoolExecutor
import jack
from .music_data import build_track_data, SongInfo, Song, map_dubs_type
from .jack_client import J_CLIENT, MUSIC_L, MUSIC_R
from .mpris_dbus import SPOTIFY_INTERFACE
from .flags import OPTIONS as opt

_EVENTS_LOCK = Event()
EVENTS_POOL = ThreadPoolExecutor(thread_name_prefix='Event')
CURR_SONG: Song = None
CURR_SONG_LOCK = Lock()
PLAYING = Event()
PLAYING.clear()
CHANNELS = 2
BITRATE = 48000


@J_CLIENT.set_process_callback
def process(frames):
    """This method is continuosly called every cicle within the JACK thread
    where I can access the buffers, must be realtime"""
    assert frames == J_CLIENT.blocksize
    l_buffer = MUSIC_L.get_array()
    r_buffer = MUSIC_R.get_array()
    if not PLAYING.is_set() or CURR_SONG is None:
        # Keep the frames going, just ignore them if paused or something
        return
    if not CURR_SONG_LOCK.acquire(blocking=False):
        return
    CURR_SONG.write_buffer(l_buffer, r_buffer)
    CURR_SONG_LOCK.release()


@J_CLIENT.set_xrun_callback
def got_xrun(usecs):
    if usecs < 0.0001:
        l.debug('Minor XRun, %lfusecs', usecs)
        return
    l.warning('Jack just had a XRun, and lost %.4fusecs, is the CPU under '
              'heavy load?', usecs)


def finish_jack():
    with CURR_SONG_LOCK:
        if CURR_SONG is not None:
            CURR_SONG.flush(opt.strict_length)


def song_event_thread(status, dicta, play):
    l.debug('Got song event, the status is: %s', status)
    was_playing = PLAYING.is_set()
    CURR_SONG_LOCK.acquire()
    try:
        global CURR_SONG
        if dicta['mpris:trackid'].startswith('spotify:ad'):
            PLAYING.clear()
            if CURR_SONG is not None:
                CURR_SONG.flush()
                CURR_SONG = None
            l.info('Advertisement, ignoring. Will try to skip it.')
            SPOTIFY_INTERFACE.Next()
            return
        song_info = build_track_data(dicta)
        # if there were a song
        if CURR_SONG is not None:
            # If the same song
            if song_info.title == CURR_SONG.info.title:
                if play and not was_playing:
                    # Just resuming a song should not flush
                    l.info('Resuming the recording!')
                    return
                if CURR_SONG.duration > 2:
                    # Probaly something like adding the song, toggling shulle...
                    # Not the initial, succesive 2-3 events of loading
                    l.debug('Got an playing event of the same song, midway '
                            'though it, maybe added to library or ')
                    return
            CURR_SONG.flush(opt.strict_length)
        if CURR_SONG is None or CURR_SONG.info.title != song_info.title:
            l.info('Started recording %s by %s',
                   song_info.title, song_info.artist[0])
        song = Song(song_info, out_format=opt.format, file_path=opt.output,
                    target_folder=opt.target)
        CURR_SONG = song
    finally:
        CURR_SONG_LOCK.release()
        # I have to propositally stale this thread or else I have to handle
        # spotify's repeated dbus events of the same song.
        time.sleep(0.5)


def song_event_handler(*args, **_):
    if len(args) <= 0 or not args[0].startswith('org.mpris.MediaPlayer2'):
        return
    status = args[1].get('PlaybackStatus', '')
    dicta: dict = args[1].get('Metadata', dict())
    play = status == 'Playing'

    if play:
        PLAYING.set()
    else:
        PLAYING.clear()
        l.info('Got pause event, waiting.')
        return

    if _EVENTS_LOCK.is_set():
        return
    _EVENTS_LOCK.set()
    EVENTS_POOL.submit(song_event_thread, status, dicta, play) \
        .add_done_callback(lambda _: _EVENTS_LOCK.clear())
