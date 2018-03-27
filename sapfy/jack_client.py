import jack
from .logger import LOGGER as l
from .flags import OPTIONS
J_CLIENT: jack.Client = None
MUSIC_L: jack.OwnPort = None
MUSIC_R: jack.OwnPort = None

try:
    if (not OPTIONS.ads_only and jack.version()):
        J_CLIENT: jack.Client = jack.Client('Sapfy', no_start_server=True)
        MUSIC_L: jack.OwnPort = J_CLIENT.inports.register(
            'sapper-left', is_terminal=True)
        MUSIC_R: jack.OwnPort = J_CLIENT.inports.register(
            'sapper-right', is_terminal=True)
except jack.JackError:
    l.error("Couldn't connect to JACK server, falling back to ad-skipping, use"
            " -a to disable this warning")
    OPTIONS.ads_only = True
except jack._ffi.error:
    l.error("Jack not installed, failling back to ad-skipping")
    OPTIONS.ads_only = True
