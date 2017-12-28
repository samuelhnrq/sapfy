# pylint: disable=C0111
"""Module intended to handle song metadata operations"""
from collections import namedtuple
import logging as l
import os.path as path
import os
import numpy as np
import soundfile as sf
import dbus
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


def in_range(x, y, diff):
    return x < y + diff and x > y - diff


class Song:
    """The class intended to represent the file and metadata of a song.
    Be careful, instanciating this class immediatly creates (and overwrites)
    the recipient file for the song"""

    def __init__(self, info, out_format='FLAC', target_folder='./',
                 file_path='{albumArtist[0]}/{album}/{trackNumber} {title}'):
        self.info: SongInfo = build_track_data(info) \
            if not isinstance(info, SongInfo) else info
        # TODO Custom output file location
        self.file_name = path.normpath(file_path.format(**self.info._asdict()))
        self.file_name += f'.{out_format.lower()}'
        self.file_name = path.join(target_folder, self.file_name)
        folder = path.dirname(self.file_name)
        if not path.exists(folder):
            os.makedirs(folder, mode=0o755)
        self.sound_file = sf.SoundFile(
            self.file_name,
            mode='w',
            samplerate=J_CLIENT.samplerate,
            channels=2,
            format=out_format)

    @property
    def duration(self):
        return len(self.sound_file) / self.sound_file.samplerate

    def flush(self, max_diff=2**64):
        if self.sound_file.closed:
            return
        self.sound_file.close()
        if self.duration > 3:
            l.info("Flushed %s to disk successfully", self.file_name)
        else:
            return
        if not in_range(self.duration, self.info.length, 2):
            l.warning('Actual song length was %dsecs when metadata said it'
                      ' would be %dsecs.', self.duration, self.info.length)
            l.warning('Was the song started half-way or interrupted?')
        if not in_range(self.duration, self.info.length, max_diff):
            l.info('The recording differs more than %dsecs from the metadata'
                   ' lenght. Erasing it, as requested.', max_diff)
            os.remove(self.file_name)

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
    filtered['length'] = dbus_dict.get('mpris:length', 0) / 1000000
    final = SongInfo(*filtered.values())
    return final
