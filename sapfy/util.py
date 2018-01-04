from threading import Lock
import dbus


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


class Counter:
    """Atomic counter."""

    def __init__(self, init_value=0):
        self._lock = Lock()
        self._val = init_value

    def add(self, val=1):
        """Atomically increases the counter by val"""
        with self._lock:
            self._val += val

    def __str__(self):
        with self._lock:
            return str(self._val)
