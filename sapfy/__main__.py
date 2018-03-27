# pylint: disable=C0413,W0603,C0111,W1202
"""Receiver related functionality."""
from .logger import LOG_LISTENER, LOG_HANDLER, LOGGER as l, shutdown
from threading import Thread
from os import path, makedirs
import signal
import numpy as _  # For the sideeffects

from . import song_event_handler, finish_jack, song_event_thread
from .flags import OPTIONS as options
from .jack_client import J_CLIENT, MUSIC_L, MUSIC_R
from .mpris_dbus import LOOP, SPOTIFY_OBJECT

l.setLevel(options.v)
EVENTS_THREAD = Thread(name='Events', target=song_event_thread)


def ending(*_):
    LOOP.quit()
    if (not options.ads_only):
        J_CLIENT.deactivate()
        J_CLIENT.close()
        finish_jack()
    LOG_LISTENER.stop()
    shutdown()


def main():
    folder = options.target
    if not path.exists(folder):
        makedirs(folder, mode=0o755)

    signal.signal(signal.SIGTERM, ending)
    SPOTIFY_OBJECT.connect_to_signal('PropertiesChanged', song_event_handler,
                                     'org.freedesktop.DBus.Properties')
    l.info("Now listening to dbus media events.")
    try:
        if (not options.ads_only):
            J_CLIENT.activate()
            sinks = J_CLIENT.get_ports('spotify*')
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
