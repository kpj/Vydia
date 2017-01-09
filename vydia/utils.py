"""
Various utility functions
"""

import os
import json, time
import datetime
import collections


def load_state(fname='state.json'):
    """ Load state
    """
    if not os.path.isfile(fname):
        res = {}
    else:
        with open(fname) as fd:
            res = json.load(fd)

    return collections.defaultdict(dict, res)

def save_state(state, fname='state.json'):
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
