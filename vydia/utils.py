"""
Various utility functions
"""

import time
import datetime


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
