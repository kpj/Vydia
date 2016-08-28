"""
Main interface
"""

import os, re
import sys
import json, time
import inspect
import datetime
import threading
import collections

from interface import App
from player import Player


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

def ts2sec(ts):
    x = time.strptime(ts, '%H:%M:%S')
    sec = datetime.timedelta(
        hours=x.tm_hour,
        minutes=x.tm_min,
        seconds=x.tm_sec).total_seconds()
    return sec

def sec2ts(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return '{:02}:{:02}:{:02}'.format(h, m, s)

class Vydia(object):
    def __init__(self, _id):
        self.playlist = self.load_playlist(_id)
        self.app = None
        self.ts = None
        self.current_vid = None

        self.mpv = Player(
            self.handle_mpv_pos,
            self.handle_mpv_event)
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

    def play_video(self, vid, start_pos=0):
        self.current_vid = vid

        def tmp():
            self.mpv.play_video(vid.stream, start=start_pos)
            self.mpv.mpv.wait_for_playback()

        t = threading.Thread(target=tmp)
        t.start()

    def handle_mpv_pos(self, pos):
        if not pos is None:
            self.ts = int(pos)
            self.footer_info('Playing ({})'.format(sec2ts(self.ts)))

    def handle_mpv_event(self, ev):
        if ev['event_id'] == 7: # end-file
            reason = ev['event']['reason']
            if reason == 0: # graceful shutdown
                self.onVideoEnd(
                    self.current_vid.title, self.ts,
                    play_next=True)
            elif reason == 2: # force quit
                self.footer_info('Waiting for input')
                self.onVideoEnd(
                    self.current_vid.title, self.ts)

    def footer_info(self, msg):
        self.app.info_bar.set_text(msg)
        self.app.loop.draw_screen()

    def assemble_info_box(self):
        wid = self.app.info_box.base_widget

        if self.playlist.title in self._state:
            cur = self._state[self.playlist.title]['current']

            wid.set_text('Resume: {} ({})'.format(
                cur['title'], cur['timestamp']))
        else:
            wid.set_text('Nothing to resume')

        if self.app.loop.screen._started:
            self.app.loop.draw_screen()

    def onSelect(self, title):
        self.footer_info('Loading video ({})'.format(title))
        self.play_video(self.playlist.get_video_by_title(title)[1])

    def onKey(self, key):
        if key in ['C', 'c']:
            if self.playlist.title in self._state:
                _cur = self._state[self.playlist.title]['current']

                i, vid = self.playlist.get_video_by_title(_cur['title'])
                self.footer_info('Resuming "{}" at {}'.format(_cur['title'], _cur['timestamp']))

                self.play_video(vid, ts2sec(_cur['timestamp']))

    def onVideoEnd(self, title, ts, play_next=False):
        self._state[self.playlist.title] = {
            'current': {
                'title': title,
                'timestamp': sec2ts(ts)
            }
        }

        save_state(self._state)
        self.assemble_info_box()

        if play_next:
            vid = self.get_next_video()
            self.footer_info('Autoplay next video in playlist ({})'.format(vid.title))
            self.play_video(vid)

    def get_next_video(self):
        idx, _ = self.playlist.get_video_by_title(self.current_vid.title)
        return self.playlist._videos[idx+1]

def main():
    """ Main interface
    """
    if len(sys.argv) != 2:
        print('Usage: {} <playlist id>'.format(sys.argv[0]))
        exit(-1)

    vyd = Vydia(sys.argv[1])
    vyd.run()

if __name__ == '__main__':
    main()
