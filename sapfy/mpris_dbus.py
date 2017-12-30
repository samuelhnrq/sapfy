# pylint: disable=C0413
import dbus as _dbus
import dbus.glib as _  # For the side effects
import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib as gobject

LOOP = gobject.MainLoop()
SESSION_BUS = _dbus.SessionBus()
SPOTIFY_OBJECT = SESSION_BUS.get_object(
    'org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
SPOTIFY_INTERFACE = _dbus.Interface(
    SPOTIFY_OBJECT, 'org.mpris.MediaPlayer2.Player')
