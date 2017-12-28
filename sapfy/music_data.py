# pylint: disable=C0111
"""Module intended to handle song metadata operations"""
from collections import namedtuple
import numpy as np
import soundfile as sf
import dbus
import logging as l
from .jack_client import J_CLIENT

SongInfo = namedtuple("SongInfo", [
    "album",
    "albumArtist",
    "artist",
    "autoRating",
    "discNumber",
    "title",
    "trackNumber",
    "length",
])


class Song:
    def __init__(self, info):
        self.info: SongInfo = build_track_data(info) \
            if not isinstance(info, SongInfo) else info
        # TODO Custom output file location
        if self.info.title == 'dummy' and self.info.artist == 'dummy':
            return
        self.file_name = f'./{self.info.title} by {self.info.artist[0]}.flac'
        self.sound_file = sf.SoundFile(
            self.file_name,
            mode='w',
            samplerate=J_CLIENT.samplerate,
            channels=2,
            format='FLAC')

    def flush(self):
        self.sound_file.close()
        if len(self.sound_file) > 5000:
            l.info("Finished flushing %s to disk", self.file_name)

    def write_buffer(self, l_channel, r_channel):
        self.sound_file.write(
            np.array([l_channel, r_channel], copy=False).transpose())


def map_dubs_type(obj):
    obj_type = type(obj)
    if obj_type == dbus.String:
        return str(obj).replace('/', '-')
    elif obj_type == dbus.Array:
        return [map_dubs_type(x) for x in obj]
    elif obj_type == dbus.Double:
        return float(obj)
    elif obj_type == dbus.Int32:
        return int(obj)
    elif obj_type == dbus.Dictionary:
        return {map_dubs_type(k): map_dubs_type(v) for k, v in obj.items()}
    else:
        return obj


def build_track_data(dbus_dict: dict) -> SongInfo:
    filtered = {str(k)[6:]: map_dubs_type(v)
                for (k, v) in dbus_dict.items() if 'xesam:' in k}
    filtered['autoRating'] = 5 * filtered.get('autoRating', 0)
    filtered.pop('url', '')
    filtered['length'] = (dbus_dict.get('mpris:length', 0) / 1000000) / 60
    final = SongInfo(*filtered.values())
    return final
