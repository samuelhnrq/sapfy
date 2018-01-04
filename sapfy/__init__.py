# pylint: disable=W0603
import logging as l
import wave as wav
import time
from collections import deque
from queue import Queue, Empty
from threading import Event, Lock, RLock
from concurrent.futures import ThreadPoolExecutor
import jack
from .music_data import build_track_data, SongInfo, Song, map_dubs_type
from .jack_client import J_CLIENT, MUSIC_L, MUSIC_R
from .mpris_dbus import SPOTIFY_INTERFACE
from .flags import OPTIONS as opt

EVENTS_POOL = ThreadPoolExecutor(thread_name_prefix='Event')
EVENTS_LOCK = Event()
EVENTS_LOCK.clear()
SONG: Song = None
SONG_LOCK = Lock()
PLAYING = Event()
PLAYING.clear()
TIMER_LOCK = RLock()
LAST_EVENT = time.monotonic()


@J_CLIENT.set_process_callback
def process(frames):
    """This method is continuosly called every cycle within the JACK thread
    where I can access the buffers, must be realtime"""
    assert frames == J_CLIENT.blocksize
    l_buffer = MUSIC_L.get_array()
    r_buffer = MUSIC_R.get_array()
    if not PLAYING.is_set() or not SONG:
        # Keep the frames going, just ignore them if paused or something
        return
    if not SONG_LOCK.acquire(blocking=False):
        return
    SONG.write_buffer(l_buffer, r_buffer)
    SONG_LOCK.release()


@J_CLIENT.set_xrun_callback
def got_xrun(duration):
    if SONG is None:
        return
    SONG.got_xrun(duration)


def finish_jack():
    with SONG_LOCK:
        if SONG is not None:
            SONG.flush(opt.strict_length)


def song_event_thread(dicta):
    """This is a function that is run as a daemon each time to actually handle
    changing the song."""
    SONG_LOCK.acquire()
    try:
        global SONG
        if dicta['mpris:trackid'].startswith('spotify:ad'):
            PLAYING.clear()
            if SONG is not None:
                SONG.flush()
                SONG = None
            l.info('Advertisement, ignoring. Will try to skip it.')
            SPOTIFY_INTERFACE.Next()
            return
        song_info = build_track_data(dicta)
        # if there were a song
        if SONG:
            # If the same song
            if song_info.title == SONG.info.title:
                # Probably adding the song, toggling shuffle...
                # Not the initial, successive 2-3 events of loading
                l.debug('Got an playing event of the same song, midway '
                        'though it.')
                return
            SONG_LOCK.release()
            time.sleep(.07)
            delta = time.monotonic() - LAST_EVENT
            if delta > 2:
                # The song wasn't none and has been more than 2 seconds
                # since last event, therefore the song is ending normally
                # spotify sends events beforehand, so we release the lock
                # and stale here for the 500ms
                l.debug("Song finished normally will stale")
                time.sleep(1.93)
                # This is just gross. Spotify shouldn't send events beforehand
            SONG_LOCK.acquire()
            SONG.flush(opt.strict_length)
        song = Song(song_info, out_format=opt.format, file_path=opt.output,
                    target_folder=opt.target)
        l.info('Started recording %s by %s',
               song_info.title, song_info.artist[0])
        SONG = song
    finally:
        SONG_LOCK.release()
        time.sleep(.5)


def event_done(inp=0):
    if inp != 0:
        EVENTS_LOCK.clear()
        l.debug('Event handling done')
    with TIMER_LOCK:
        global LAST_EVENT
        LAST_EVENT = time.monotonic()


def song_event_handler(*args, **kwargs):
    """This is a function that is connected to the spotify mpris event
    emitter and is called with each new spotify event."""
    status = args[1].get('PlaybackStatus', '')
    dicta: dict = args[1].get('Metadata', dict())

    if status == 'Playing':
        PLAYING.set()
    else:
        PLAYING.clear()
        l.info('Got pause event, waiting.')
        event_done()
        return

    if EVENTS_LOCK.is_set():
        l.debug("Ignoring repeated event")
        event_done()
        return
    EVENTS_LOCK.set()
    EVENTS_POOL.submit(song_event_thread, dicta) \
        .add_done_callback(event_done)
