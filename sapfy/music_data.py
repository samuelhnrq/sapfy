# pylint: disable=C0111
"""Module intended to handle song metadata operations"""
from collections import namedtuple
import logging as l
import os.path as path
import os
import mutagen as mt
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


def within_diff(val, target, diff):
    """The name of this method is really bad, basically it returns whether or not
    is val within diff away from target"""
    return val < target + diff and val > target - diff


class Song:
    """The class intended to represent the file and metadata of a song.
    Be careful, instanciating this class immediately creates (and overwrites)
    the recipient file for the song"""

    # TODO XRun counter
    def __init__(self, info, out_format='FLAC', target_folder='./',
                 file_path='{albumArtist[0]}/{album}/{trackNumber} {title}'):
        self.info: SongInfo = build_track_data(info) \
            if not isinstance(info, SongInfo) else info
        self.file_name = path.normpath(file_path.format(**self.info._asdict()))
        self.file_name += f'.{out_format.lower()}'
        self.file_name = path.join(target_folder, self.file_name)
        folder = path.dirname(self.file_name)
        if not path.exists(folder):
            os.makedirs(folder, mode=0o755)
        # TODO Compression configuration?
        self.sound_file = sf.SoundFile(
            self.file_name,
            mode='w',
            samplerate=J_CLIENT.samplerate,
            channels=2,
            format=out_format)

    @staticmethod
    def info_to_metadata(info: dict):
        for k, val in info.items():
            if isinstance(val, str):
                continue
            if isinstance(val, list):
                val = ', '.join(val)
            else:
                val = str(val)
            info[k] = val
        return info

    @property
    def duration(self):
        return len(self.sound_file) / self.sound_file.samplerate

    def flush(self, max_diff=1500):
        # TODO Support for custom --exec flag with the output files
        if self.sound_file.closed:
            return
        self.sound_file.close()
        if self.duration > 2:
            l.info("Flushed %s to disk successfully",
                   path.basename(self.file_name))
        # Do warn the user, regardless if strict or not.
        if not within_diff(self.duration, self.info.length, 4):
            l.warning('Actual song length was %dsecs when metadata said it'
                      ' would be %dsecs.', self.duration, self.info.length)
            l.warning('Was the song started half-way or interrupted?')
        if not within_diff(self.duration, self.info.length, max_diff):
            l.info('The recording differs more than %dsecs from the metadata'
                   ' lenght. Erasing it, as requested.', max_diff)
            os.remove(self.file_name)
            return
        metadata: mt.FileType = mt.File(self.file_name)
        metadata.update(Song.info_to_metadata(self.info._asdict()))
        metadata.save()

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
    elif obj_type in (dbus.Int16, dbus.Int32, dbus.Int64):
        return int(obj)
    elif obj_type == dbus.Dictionary:
        return {map_dubs_type(k): map_dubs_type(v) for k, v in obj.items()}
    return obj


def build_track_data(dbus_dict: dict) -> SongInfo:
    filtered = {str(k)[6:]: map_dubs_type(v)
                for (k, v) in dbus_dict.items() if 'xesam:' in k}
    filtered['autoRating'] = 5 * filtered.get('autoRating', 0)
    filtered.pop('url', '')
    filtered['length'] = dbus_dict.get('mpris:length', 0) / 1000000
    final = SongInfo(*filtered.values())
    return final
