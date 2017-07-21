"""
Various utility functions
"""

import time
import datetime
import subprocess


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
    return int(sec)

def sec2ts(sec):
    return time.strftime("%H:%M:%S", time.gmtime(sec))

def get_video_duration(fname):
    result = subprocess.Popen(['ffprobe', fname],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    dur_lines = [x.decode()
                 for x in result.stdout.readlines() if b'Duration' in x]
    assert len(dur_lines) == 1

    dur_str = dur_lines[0].split()[1].split('.')[0]
    return ts2sec(dur_str)
