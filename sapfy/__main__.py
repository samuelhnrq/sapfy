# pylint: disable=C0413,W0603,C0111,W1202
"""Receiver related functionality."""
import logging as l
import logging.handlers as lh
import signal
import queue
from os import environ, path, makedirs
from threading import Thread
import numpy as _  # For the sideeffects
from . import song_event_handler, finish_jack, song_event_thread
from .jack_client import J_CLIENT, MUSIC_L, MUSIC_R
from .flags import OPTIONS as options
from .mpris_dbus import LOOP, SPOTIFY_OBJECT

EVENTS_THREAD = Thread(name='Events', target=song_event_thread)


def ending(*_):
    LOOP.quit()
    J_CLIENT.deactivate()
    J_CLIENT.close()
    finish_jack()
    LOG_LISTENER.stop()
    l.shutdown()


def setup_logging():
    root_logger = l.getLogger()
    root_logger.setLevel(options.v)

    file_formatter = l.Formatter(
        "%(asctime)s [%(threadName)-10.10s] [%(levelname)-5.5s]: %(message)s")
    file_handler = l.FileHandler(environ.get('HOME', '.') + '/.sapfy.log')
    file_handler.setFormatter(file_formatter)

    log_formatter = l.Formatter(
        "%(asctime)s [%(levelname)-5.5s]: %(message)s",
        datefmt='%H:%M:%S')
    console_handler = l.StreamHandler()
    console_handler.setFormatter(log_formatter)

    log_queue = queue.Queue(-1)
    queue_handler = lh.QueueHandler(log_queue)
    queue_listener = lh.QueueListener(log_queue, console_handler, file_handler)
    root_logger.addHandler(queue_handler)
    queue_listener.start()
    return queue_listener


LOG_LISTENER = setup_logging()


def main():
    folder = options.target
    if not path.exists(folder):
        makedirs(folder, mode=0o755)

    signal.signal(signal.SIGTERM, ending)
    SPOTIFY_OBJECT.connect_to_signal(
        'PropertiesChanged', song_event_handler,
        'org.freedesktop.DBus.Properties')
    l.info("Now listening to dbus media events.")
    sinks = J_CLIENT.get_ports('spotify*')
    try:
        J_CLIENT.activate()
        MUSIC_L.connect(sinks[0])
        MUSIC_R.connect(sinks[1])
        LOOP.run()
    except KeyboardInterrupt:
        print()
        l.info("Got interrupt, exiting gracefully.")
    except IndexError:
        # I could've null checked the array to see if it weren't empty
        # but I do want it to blow up if it doesn't find a sink.
        l.error("Couldn't find any jack source or port named spotify")
        l.error('Have you created the jack -> pulse sink?')
    finally:
        ending()


main()
