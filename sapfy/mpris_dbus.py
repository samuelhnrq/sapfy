# pylint: disable=C0413
import dbus as _dbus
import dbus.glib as _  # For the side effects
import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib as gobject
import sys
import logging as l

LOOP = gobject.MainLoop()
SESSION_BUS = _dbus.SessionBus()
SPOTIFY_OBJECT: _dbus.proxies.ProxyObject = None
SPOTIFY_INTERFACE: _dbus.proxies.Interface = None
try:
    SPOTIFY_OBJECT = SESSION_BUS.get_object('org.mpris.MediaPlayer2.spotify',
                                            '/org/mpris/MediaPlayer2')
    SPOTIFY_INTERFACE = _dbus.Interface(SPOTIFY_OBJECT,
                                        'org.mpris.MediaPlayer2.Player')
except _dbus.DBusException as ex:
    if ex.get_dbus_name() == 'org.freedesktop.DBus.Error.ServiceUnknown':
        l.error("Spotify isn't running right now!")
        sys.exit(1)
