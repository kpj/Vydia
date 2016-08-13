"""
Main interface
"""

import os, re
import json, time
import inspect
import threading
import subprocess
import collections

from interface import App


def load_state():
    """ Load state
    """
    fname = 'state.json'

    if not os.path.isfile(fname):
        res = {}
    else:
        with open(fname) as fd:
            res = json.load(fd)

    return collections.defaultdict(dict, res)

def save_state(state):
    fname = 'state.json'

    with open(fname, 'w') as fd:
        json.dump(state, fd)

def get_plugins():
    """ Return list of available plugins
    """
    import plugins
    for Cls in plugins.BasePlugin.__subclasses__():
        yield Cls

class Vydia(object):
    def __init__(self, _id):
        self.playlist = self.load_playlist(_id)
        self.app = None

        self._state = load_state()

    def load_playlist(self, _id):
        for Plg in get_plugins():
            plugin = Plg()
            playlist = plugin.extract_playlist(_id)
            if not playlist is None:
                print('Loaded playlist with {}'.format(Plg.__name__))
                return playlist
        raise RuntimeError('Playlist could not be loaded')

    def run(self):
        self.app = App(
            self.playlist.title, [vid.title for vid in self.playlist],
            self.onSelect, self.onKey)

        self.assemble_info_box()
        self.app.run()

    def play_video(self, vid, start_cmd=''):
        proc = subprocess.Popen(
            ['mpv', start_cmd, '--title={}'.format(vid.title), vid.stream],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=1)

        ts, buf = '', ''
        pat = re.compile(r'.{,15}AV?:\s*(\d\d):(\d\d):(\d\d)')
        while proc.poll() is None:
            out = proc.stderr.read(1).decode('utf-8', errors='ignore')
            if out in '\r\n':
                match = pat.match(buf)
                if match:
                    h, m, s = map(int, match.groups())
                    ts = '{:02}:{:02}:{:02}'.format(h, m, s)

                    self.footer_info('Playing ({})'.format(ts))
                buf = ''
            else:
                buf += out

        self.onVideoEnd(vid.title, ts)
        self.footer_info('Waiting for input')

    def footer_info(self, msg):
        self.app.info_bar.set_text(msg)
        self.app.loop.draw_screen()

    def assemble_info_box(self):
        wid = self.app.info_box.base_widget
        cur = self._state[self.playlist.title]['current']

        wid.set_text('Current: {} ({})'.format(
            cur['title'], cur['timestamp']))

    def onSelect(self, title):
        self.footer_info('Loading video ({})'.format(title))

        t = threading.Thread(
            target=self.play_video,
            args=(self.playlist.get_video_by_title(title),))
        t.start()

    def onKey(self, key):
        if key in ['C', 'c']:
            if self.playlist.title in self._state:
                _cur = self._state[self.playlist.title]['current']
                start_cmd = '--start={}'.format(_cur['timestamp'])

                vid = self.playlist.get_video_by_title(_cur['title'])
                self.footer_info('Resuming "{}" at {}'.format(_cur['title'], _cur['timestamp']))

                self.play_video(vid, start_cmd)

    def onVideoEnd(self, title, ts):
        self._state[self.playlist.title] = {
            'current': {
                'title': title,
                'timestamp': ts
            }
        }

        save_state(self._state)
        self.assemble_info_box()

def main():
    """ Main interface
    """
    vyd = Vydia(input('Enter playlist id\n-> '))
    vyd.run()

if __name__ == '__main__':
    main()
