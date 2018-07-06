"""
Various utility functions
"""

import time
import datetime

from typing import Iterable, Type, Tuple, Dict, Any, TYPE_CHECKING

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

if TYPE_CHECKING:
    from .plugins import BasePlugin, Playlist  # noqa: F401


def get_plugins() -> Iterable[Type['BasePlugin']]:
    """ Return list of available plugins
    """
    from .plugins import BasePlugin  # noqa: F811
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
    with createParser(fname) as parser:
        try:
            metadata = extractMetadata(parser)
        except Exception as err:
            return -1

    return metadata.get('duration').seconds


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
            cur_dict[k] = nested_dict_update(old_val, v) if isinstance(old_val, dict) else v
        else:
            cur_dict[k] = v
    return cur_dict


def shorten_msg(text: str, width: int, suffix: str = '[...]') -> str:
    if len(text) <= width:
        return text
    else:
        return text[:width-len(suffix)] + suffix
