"""
Main interface
"""

import time
import threading

from .interface import IntroScreen, App
from .player import Player
from .utils import *


class Vydia(object):
    def __init__(self, _id):
        self.id = _id

        self.playlist = None
        self.app = None
        self.ts = None
        self.current_vid = None

        self.mpv = Player(
            self.handle_mpv_pos,
            self.handle_mpv_event)
        self._state = load_state()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.onVideoEnd()
        save_state(self._state)
        del self.mpv

    def initial_loading(self):
        time.sleep(.1) # horrible, but how else?
        self.footer_info('Loading...')

        self.playlist = self.load_playlist(self.id)
        if self.playlist.title not in self._state:
            self._state[self.playlist.title] = {
                'id': self.id
            }
            save_state(self._state)

        self.app.set_title(self.playlist.title)
        self.app.set_items(['{} ({})'.format(vid.title, sec2ts(vid.duration)) for vid in self.playlist])
        self.assemble_info_box()

    def load_playlist(self, _id):
        for Plg in get_plugins():
            plugin = Plg()
            playlist = plugin.extract_playlist(_id)
            if playlist is not None:
                self.footer_info('Loaded playlist with {}'.format(Plg.__name__))
                return playlist
        raise RuntimeError('Playlist could not be loaded')

    def run(self):
        # prefetch playlist title if possible
        prelim_title = 'Loading...'
        for title, data in self._state.items():
            if data['id'] == self.id:
                prelim_title = title
                break

        # setup app
        self.app = App(
            prelim_title, [],
            self.onSelect, self.onKey)

        self.app.init_app()
        threading.Thread(target=self.initial_loading).start()
        self.app.run()

    def play_video(self, vid, start_pos=0):
        self.current_vid = vid

        def tmp():
            self.mpv.play_video(vid.stream, start=start_pos)
            self.mpv.mpv.wait_for_playback()

        t = threading.Thread(target=tmp)
        t.start()

    def handle_mpv_pos(self, pos):
        if pos is not None:
            self.ts = int(pos)
            self.footer_info('Playing ({})'.format(sec2ts(self.ts)))

    def handle_mpv_event(self, ev):
        if ev['event_id'] == 7: # end-file
            reason = ev['event']['reason']
            if reason == 0: # graceful shutdown
                self.onVideoEnd(play_next=True)
            elif reason == 2: # force quit
                self.footer_info('Waiting for input')
                self.onVideoEnd()

    def footer_info(self, msg):
        self.app.info_bar.set_text(msg)
        #if self.app.loop._started:
        self.app.loop.draw_screen()

    def assemble_info_box(self):
        wid = self.app.info_box.base_widget

        if 'current' in self._state[self.playlist.title]:
            cur = self._state[self.playlist.title]['current']

            wid.set_text('Resume: {} ({})'.format(
                cur['title'], cur['timestamp']))
        else:
            wid.set_text('Nothing to resume')

        if self.app.loop.screen._started:
            self.app.loop.draw_screen()

    def onSelect(self, title):
        clean_title = title[:-11] # remove length annotation

        self.footer_info('Loading video ({})'.format(clean_title))
        self.play_video(self.playlist.get_video_by_title(clean_title)[1])

    def onKey(self, key):
        if key in ['C', 'c']:
            if self.playlist.title in self._state:
                _cur = self._state[self.playlist.title]['current']

                i, vid = self.playlist.get_video_by_title(_cur['title'])
                self.footer_info('Resuming "{}" at {}'.format(_cur['title'], _cur['timestamp']))

                self.play_video(vid, ts2sec(_cur['timestamp']))

    def onVideoEnd(self, play_next=False):
        if self.current_vid is not None:
            self._state[self.playlist.title].update({
                'current': {
                    'title': self.current_vid.title,
                    'timestamp': sec2ts(self.ts)
                }
            })

        save_state(self._state)
        self.assemble_info_box()

        if play_next:
            vid = self.get_next_video()
            if vid is None:
                self.footer_info('Reached end of playlist')
            else:
                self.footer_info('Autoplay next video in playlist ({})'.format(vid.title))
                self.play_video(vid)

    def get_next_video(self):
        idx, _ = self.playlist.get_video_by_title(self.current_vid.title)
        next_idx = idx + 1

        if next_idx < len(self.playlist._videos):
            return self.playlist._videos[next_idx]
        else:
            return None

def main():
    """ Main interface
    """
    def button(playlist_id):
        with Vydia(playlist_id) as vyd:
            vyd.run()

    def selection(playlist_name):
        button(load_state()[playlist_name]['id'])

    playlists = sorted(load_state().keys())

    intro = IntroScreen(
        'Existing playlists', playlists,
        onSelect=selection, onButton=button)
    intro.run()

if __name__ == '__main__':
    main()