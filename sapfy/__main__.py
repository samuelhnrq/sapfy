# pylint: disable=C0413,W0603,C0111,W1202
"""Receiver related functionality."""
import logging as l
import signal
import dbus.service
import dbus.glib
import dbus
import numpy as _  # For the sideeffects
import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib as gobject
from . import song_event_handler, finish_jack
from .jack_client import J_CLIENT, MUSIC_L, MUSIC_R
from .flags import PARSER


LOOP = gobject.MainLoop()


def ending(*_):
    print()
    l.info("Got interrupt, exiting gracefully.")
    LOOP.quit()
    J_CLIENT.deactivate()
    J_CLIENT.close()
    finish_jack()
    l.shutdown()


def setup_logging(options):
    root_logger = l.getLogger()
    root_logger.setLevel(options.v)

    log_formatter = l.Formatter(
        "%(asctime)s [%(threadName)-10.10s] [%(levelname)-5.5s]: %(message)s")

    file_handler = l.FileHandler('sapfy.log')
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    root_logger.info('{0} STARTING UP! {0}'.format('-' * 12))

    console_handler = l.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


def main():
    options = PARSER.parse_args()
    setup_logging(options)

    s_bus = dbus.SessionBus()
    s_bus.add_signal_receiver(
        song_event_handler,
        interface_keyword='dbus_interface',
        dbus_interface='org.freedesktop.DBus.Properties',
        signal_name='PropertiesChanged',
        member_keyword='member')
    signal.signal(signal.SIGTERM, ending)
    l.info("Now listening to dbus media events.")
    sinks = J_CLIENT.get_ports('spotify*')
    try:
        J_CLIENT.activate()
        MUSIC_L.connect(sinks[0])
        MUSIC_R.connect(sinks[1])
        LOOP.run()
    except KeyboardInterrupt:
        ending()


main()
