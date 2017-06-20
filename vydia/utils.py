"""
Various utility functions
"""

import os
import json, time
import datetime
import collections
from pathlib import Path

from appdirs import AppDirs


adirs = AppDirs('vydia', 'kpj')
CONFIG_FILE = Path(adirs.user_config_dir) / 'state.json'

def ensure_dir(fname):
    """ Make sure that directory exists
    """
    dir_ = os.path.dirname(fname)
    if not os.path.isdir(dir_):
        os.makedirs(dir_)

def load_state(fname=CONFIG_FILE):
    """ Load state
    """
    ensure_dir(fname)

    if not os.path.isfile(fname):
        res = {}
    else:
        with open(fname) as fd:
            res = json.load(fd)

    return collections.defaultdict(dict, res)

def save_state(state, fname=CONFIG_FILE):
    ensure_dir(fname)

    with open(fname, 'w') as fd:
        json.dump(state, fd)

def get_plugins():
    """ Return list of available plugins
    """
    from .plugins import BasePlugin
    for Cls in BasePlugin.__subclasses__():
        yield Cls

def ts2sec(ts):
    x = time.strptime(ts, '%H:%M:%S')
    sec = datetime.timedelta(
        hours=x.tm_hour,
        minutes=x.tm_min,
        seconds=x.tm_sec).total_seconds()
    return sec

def sec2ts(sec):
    return time.strftime("%H:%M:%S", time.gmtime(sec))
