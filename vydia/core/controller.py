import time
import logging
import threading

import urwid

import logzero
from logzero import logger

from typing import Any, Iterable, Optional, Dict, TYPE_CHECKING

from .model import Model
from .view import View
from ..extra.player import Player
from ..extra.utils import load_playlist, sec2ts, ts2sec

if TYPE_CHECKING:
    from ..extra.plugins import Video, Playlist


class Controller:
    def __init__(self) -> None:
        self.current_playlist = None  # type: Optional[str]
        self.input_callback = None
        self.player = None  # type: Optional[PlayerQueue]

        self.model = Model()
        self.view = View(self)

        self.loop = urwid.MainLoop(
            self.view, unhandled_input=self._unhandled_input,
            palette=[('reversed', 'standout', '')])

        logzero.loglevel(logging.ERROR)
        logzero.logfile(
            self.model.LOG_FILE,
            maxBytes=1e6, backupCount=3, loglevel=logging.ERROR)

    def __enter__(self) -> 'Controller':
        logger.info(f'Create controller')
        return self

    def __exit__(
        self, exc_type: Any, exc_value: Any, traceback: Any
    ) -> None:
        self.save_state()
        if self.player is not None:
            self.player.mpv.stop()
        logger.info(f'Destroy controller')

    def main(self) -> None:
        self.view.show_playlist_overview()
        self.loop.run()

    def _unhandled_input(self, key: str) -> None:
        if key in ('Q', 'q', 'esc'):
            raise urwid.ExitMainLoop()

        if self.input_callback is not None:
            self.input_callback(key)

    def on_playlist_selected(self, playlist_id: str) -> None:
        self.current_playlist = playlist_id
        logger.info(f'Selected playlist {self.current_playlist}')

        self.view.show_episode_overview()
        self._init_player()

    def on_video_selected(self, video_id: str) -> None:
        if self.player is None:
            raise RuntimeError('Player was not instantiated')
        if self.player.playlist is None:
            raise RuntimeError('Player\'s playlist was not instantiated')

        clean_title = video_id[:-11]  # remove length annotation
        logger.info(f'Selected video {clean_title}')

        self.send_msg(f'Loading video ({clean_title})')
        vid = self.player.playlist.get_video_by_title(clean_title)[1]
        if vid is not None:
            self.player.play_video(vid)
        else:
            raise RuntimeError(f'Could not find video "{clean_title}"')

    def get_playlist_list(self) -> Iterable[str]:
        return self.model.get_playlist_list()

    def get_current_playlist_info(self) -> Dict[str, str]:
        if self.current_playlist is None:
            raise RuntimeError('Current playlist is not set')

        return self.model.get_playlist_info(self.current_playlist)

    def continue_playback(self) -> None:
        if self.player is None:
            raise RuntimeError('Player was not instantiated')
        if self.player.playlist is None:
            raise RuntimeError('Player\'s playlist was not instantiated')
        if self.current_playlist is None:
            raise RuntimeError('Current playlist is not set')
        logger.info(f'Continue playback')

        _cur = self.model.get_current_video(self.current_playlist)

        i, vid = self.player.playlist.get_video_by_title(_cur['title'])
        self.send_msg(f'Resuming "{_cur["title"]}" at {_cur["timestamp"]}')

        if vid is not None:
            self.player.play_video(vid, ts2sec(_cur['timestamp']))
        else:
            raise RuntimeError(f'Could not find video "{_cur["title"]}"')

    def _init_player(self) -> None:
        self.player = PlayerQueue(self)
        self.player.setup()

    def save_state(self) -> None:
        if self.player is not None:
            logger.info(f'Explicit state save')
            assert self.current_playlist is not None
            assert self.player.ts is not None

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
        if self.current_playlist is None:
            raise RuntimeError('Current playlist is not set')

        logger.info('Assembling info box')
        _cur = self.model.get_current_video(self.current_playlist)

        if _cur is not None:
            txt = f'Resume: "{_cur["title"]}" ({_cur["timestamp"]})'
        else:
            txt = 'Nothing to resume'

        self.view.widget.update_info_box(txt)

    def send_msg(self, msg: str) -> None:
        self.view.widget.update_info_text(msg)


class PlayerQueue:
    def __init__(self, controller: Controller) -> None:
        self.controller = controller
        self.mpv = Player(
            self.handle_mpv_pos,
            self.handle_mpv_event)

        if self.controller.current_playlist is None:
            raise RuntimeError('Current playlist is not set')
        self.id = self.controller.model.get_playlist_info(
            self.controller.current_playlist)['id']

        self.playlist = None  # type: Optional['Playlist']
        self.current_vid = None  # type: Optional['Video']
        self.ts = None  # type: Optional[int]

    def setup(self) -> None:
        def tmp() -> None:
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

    def handle_mpv_pos(self, prop_name: str, pos: float) -> None:
        assert self.current_vid is not None

        if pos is not None:
            self.ts = int(pos)
            assert self.ts is not None

            self.controller.send_msg(
                f'Playing "{self.current_vid.title}" ({sec2ts(self.ts)})')

    def handle_mpv_event(self, ev: Any) -> None:
        if ev['event_id'] == 7:  # end-file
            reason = ev['event']['reason']
            if reason == 0:  # graceful shutdown
                self.onVideoEnd(play_next=True)
            elif reason == 2:  # force quit
                self.controller.send_msg('Waiting for input')
                self.onVideoEnd()

    def onVideoEnd(self, play_next: bool = False) -> None:
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

    def play_video(self, vid: 'Video', start_pos: int = 0) -> None:
        self.current_vid = vid

        def tmp() -> None:
            self.mpv.play_video(
                vid.title, vid.get_file_stream(),
                start=start_pos)
            self.mpv.mpv.wait_for_playback()

        t = threading.Thread(target=tmp)
        t.start()

    def get_next_video(self) -> Optional['Video']:
        assert self.playlist is not None
        assert self.current_vid is not None

        idx, _ = self.playlist.get_video_by_title(self.current_vid.title)
        if idx is None:
            raise RuntimeError(
                f'Could not find video "{self.current_vid.title}"')

        next_idx = idx + 1

        if next_idx < len(self.playlist):
            return self.playlist[next_idx]
        else:
            return None
