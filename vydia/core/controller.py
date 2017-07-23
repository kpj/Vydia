import time
import logging
import threading

import urwid

from typing import Iterable

from .model import Model
from .view import View
from ..extra.player import Player
from ..extra.utils import load_playlist, sec2ts, ts2sec


class Controller:
    def __init__(self) -> None:
        self.current_playlist = None
        self.input_callback = None
        self.player = None

        self.model = Model()
        self.view = View(self)

        self.loop = urwid.MainLoop(
            self.view, unhandled_input=self._unhandled_input,
            palette=[('reversed', 'standout', '')])

        logging.basicConfig(
            filename=self.model.LOG_FILE, level=logging.DEBUG,
            format='[%(module)s|%(funcName)s] - %(message)s',
            filemode='w')

    def __enter__(self):
        logging.info(f'Create controller')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.save_state()
        logging.info(f'Destroy controller')

    def main(self) -> None:
        self.view.show_playlist_overview()
        self.loop.run()

    def _unhandled_input(self, key) -> None:
        if key in ('Q', 'q', 'esc'):
            raise urwid.ExitMainLoop()

        if self.input_callback is not None:
            self.input_callback(key)

    def on_playlist_selected(self, playlist_id: str) -> None:
        self.current_playlist = playlist_id
        logging.info(f'Selected playlist {self.current_playlist}')

        self.view.show_episode_overview()
        self._init_player()

    def on_video_selected(self, video_id: str) -> None:
        clean_title = video_id[:-11] # remove length annotation
        logging.info(f'Selected video {clean_title}')

        self.send_msg(f'Loading video ({clean_title})')
        self.player.play_video(
            self.player.playlist.get_video_by_title(clean_title)[1])

    def get_playlist_list(self) -> Iterable:
        return self.model.get_playlist_list()

    def get_current_playlist_info(self) -> dict:
        return self.model.get_playlist_info(self.current_playlist)

    def continue_playback(self) -> None:
        logging.info(f'Continue playback')

        _cur = self.model.get_current_video(self.current_playlist)

        i, vid = self.player.playlist.get_video_by_title(_cur['title'])
        self.send_msg(f'Resuming "{_cur["title"]}" at {_cur["timestamp"]}')

        self.player.play_video(vid, ts2sec(_cur['timestamp']))

    def _init_player(self) -> None:
        self.player = PlayerQueue(self)
        self.player.setup()

    def save_state(self) -> None:
        if self.player is not None:
            logging.info(f'Explicit state save')
            assert self.current_playlist is not None

            # update current video
            if self.player.current_vid is not None:
                self.model.update_state(
                    self.current_playlist, {
                        'current': {
                            'title': self.player.current_vid.title,
                            'timestamp': sec2ts(self.player.ts)
                        }
                    })

    def assemble_info_box(self) -> None:
        logging.info('Assembling info box')
        _cur = self.model.get_current_video(self.current_playlist)

        if _cur is not None:
            txt = f'Resume: "{_cur["title"]}" ({_cur["timestamp"]})'
        else:
            txt = 'Nothing to resume'

        self.view.widget.update_info_box(txt)

    def send_msg(self, msg: str) -> None:
        self.view.widget.update_info_text(msg)


class PlayerQueue:
    def __init__(self, controller):
        self.controller = controller
        self.mpv = Player(
            self.handle_mpv_pos,
            self.handle_mpv_event)

        self.id = self.controller.model.get_playlist_info(
            self.controller.current_playlist)['id']

        self.playlist = None
        self.current_vid = None
        self.ts = None

    def setup(self):
        def tmp():
            self.controller.send_msg('Loading...')

            plugin_name, self.playlist = load_playlist(self.id)
            self.controller.send_msg(
                f'Loaded playlist with {plugin_name}')

            v = self.controller.view.widget
            v.set_title(self.playlist.title)
            v.set_items(
                ['{} ({})'.format(vid.title, sec2ts(vid.duration))
                    for vid in self.playlist])
            self.controller.assemble_info_box()

        t = threading.Thread(target=tmp)
        t.start()

    def handle_mpv_pos(self, prop_name, pos):
        if pos is not None:
            self.ts = int(pos)
            self.controller.send_msg(
                f'Playing "{self.current_vid.title}" ({sec2ts(self.ts)})')

    def handle_mpv_event(self, ev):
        if ev['event_id'] == 7: # end-file
            reason = ev['event']['reason']
            if reason == 0: # graceful shutdown
                self.onVideoEnd(play_next=True)
            elif reason == 2: # force quit
                self.controller.send_msg('Waiting for input')
                self.onVideoEnd()

    def onVideoEnd(self, play_next=False):
        self.controller.save_state()
        self.controller.assemble_info_box()

        if play_next:
            vid = self.get_next_video()
            if vid is None:
                self.controller.send_msg('Reached end of playlist')
            else:
                self.controller.send_msg(
                    f'Autoplay next video in playlist ({vid.title})')
                self.play_video(vid)

    def play_video(self, vid, start_pos=0):
        self.current_vid = vid

        def tmp():
            self.mpv.play_video(vid.get_file_stream(), start=start_pos)
            self.mpv.mpv.wait_for_playback()

        t = threading.Thread(target=tmp)
        t.start()

    def get_next_video(self):
        idx, _ = self.playlist.get_video_by_title(self.current_vid.title)
        next_idx = idx + 1

        if next_idx < len(self.playlist._videos):
            return self.playlist._videos[next_idx]
        else:
            return None
