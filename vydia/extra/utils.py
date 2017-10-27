"""
Various utility functions
"""

import time
import datetime
import subprocess

from typing import Iterable, Type, Tuple, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .plugins import BasePlugin, Playlist


def get_plugins() -> Iterable[Type['BasePlugin']]:
    """ Return list of available plugins
    """
    from .plugins import BasePlugin
    for Cls in BasePlugin.__subclasses__():
        yield Cls

def ts2sec(ts: str) -> int:
    x = time.strptime(ts, '%H:%M:%S')
    sec = datetime.timedelta(
        hours=x.tm_hour,
        minutes=x.tm_min,
        seconds=x.tm_sec).total_seconds()
    return int(sec)

def sec2ts(sec: int) -> str:
    return time.strftime("%H:%M:%S", time.gmtime(sec))

def get_video_duration(fname: str) -> int:
    result = subprocess.Popen(
        ['ffprobe', fname],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    dur_lines = [x.decode()
                 for x in result.stdout.readlines() if b'Duration' in x]
    assert len(dur_lines) == 1

    dur_str = dur_lines[0].split()[1].split('.')[0]
    return ts2sec(dur_str)

def load_playlist(_id: str) -> Tuple[str, 'Playlist']:
    for Plg in get_plugins():
        plugin = Plg()
        playlist = plugin.extract_playlist(_id)
        if playlist is not None:
            return (Plg.__name__, playlist)
    raise ValueError(f'Playlist "{_id}" could not be loaded')

def nested_dict_update(
    cur_dict: Dict[Any, Any],
    update_data: Dict[Any, Any]
) -> Dict[Any, Any]:
    for k, v in update_data.items():
        if isinstance(v, dict):
            old_val = cur_dict.get(k, {})
            if isinstance(old_val, dict):
                r = nested_dict_update(old_val, v)
            else:
                r = v
            cur_dict[k] = r
        else:
            cur_dict[k] = update_data[k]
    return cur_dict
