import sys
import time
import shlex
import logging
import textwrap
import threading

import urwid

import logzero
from logzero import logger

from typing import Any, Iterable, Optional, Dict, List, TYPE_CHECKING

from .model import Model
from .view import View
from ..extra.player import PlayerEvent, BasePlayer
from ..extra.utils import load_playlist, sec2ts, ts2sec

if TYPE_CHECKING:
    from ..extra.plugins import Video, Playlist


class Controller:
    def __init__(
        self,
        player_backend: BasePlayer, config: Dict[str, Any]
    ) -> None:
        self.config = config
        self.player_backend = player_backend
        self.player_backend.set_controller(self)

        self.current_playlist = None  # type: Optional[str]
        self.input_callback = None
        self.player = None  # type: Optional[PlayerQueue]

        self.model = Model()
        self.view = View(self)

        self.loop = urwid.MainLoop(
            self.view, unhandled_input=self._unhandled_input,
            palette=[('reversed', 'standout', '')])

        self._setup_logging()

    def __enter__(self) -> 'Controller':
        logger.info(f'Create controller')
        return self

    def __exit__(
        self, exc_type: Any, exc_value: Any, traceback: Any
    ) -> None:
        self.save_state()
        if self.player is not None:
            self.player_backend.shutdown()
        logger.info(f'Destroy controller')

    def _setup_logging(self) -> None:
        # init logzero
        logzero.loglevel(logging.WARNING)
        logzero.logfile(
            self.model.LOG_FILE,
            maxBytes=1e6, backupCount=3)

        # enforce logging of unhandled exceptions
        def handle_exception(exc_type, exc_value, exc_traceback):
            logger.error(
                'Uncaught exception',
                exc_info=(exc_type, exc_value, exc_traceback))
        sys.excepthook = handle_exception

    def main(self) -> None:
        self.view.show_playlist_overview()
        self.loop.run()

    def _unhandled_input(self, key: str) -> None:
        if key in ('Q', 'q', 'esc'):
            raise urwid.ExitMainLoop()

        if key == ':':
            self.view.show_cmdline()
            return

    def handle_cmdline_input(self, msg: str) -> None:
        if len(msg) == 0:
            return

        if msg.lower() in ('q', 'quit'):
            raise urwid.ExitMainLoop()

        if self.view.widget is not None:
            cmd, *args = shlex.split(msg)
            logger.info(f'Executing command {cmd} with "{args}"')
            self.view.widget.handle_command(cmd, args=args)

    def on_playlist_selected(self, playlist_id: str) -> None:
        self.current_playlist = playlist_id
        logger.info(f'Selected playlist {self.current_playlist}')

        self.view.show_episode_overview()
        self._init_player()

    def on_video_selected(self, video_display_name: str) -> None:
        if self.player is None:
            raise RuntimeError('Player was not instantiated')
        if self.player.playlist is None or self.player.item_list is None:
            raise RuntimeError('Player\'s playlist was not instantiated')

        video_index = self.player.item_list.index(
            video_display_name)

        vid = self.player.playlist[video_index]
        logger.info(f'Selected video {vid.title}')

        self.send_msg(f'Loading video ({vid.title})')
        if vid is not None:
            self.player.play_video(vid)
        else:
            raise RuntimeError(f'Could not find video "{vid.title}"')

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

        if _cur is None:
            self.send_msg('Nothing to resume...')
            return

        i, vid = self.player.playlist.get_video_by_title(_cur['title'])
        self.send_msg(f'Resuming "{_cur["title"]}" at {_cur["timestamp"]}')

        if vid is not None:
            self.player.play_video(vid, ts2sec(_cur['timestamp']))
        else:
            raise RuntimeError(f'Could not find video "{_cur["title"]}"')

    def mark_watched(self, entry_idx: int) -> None:
        assert self.player is not None
        assert self.player.playlist is not None
        assert self.current_playlist is not None

        vid = self.player.playlist[entry_idx]
        assert vid is not None

        # mark as unwatched if already watched
        new_ts = sec2ts(vid.duration)
        _state = self.model.get_playlist_info(self.current_playlist)
        if vid.title in _state['episodes']:
            if _state['episodes'][vid.title]['current_timestamp'] == new_ts:
                new_ts = sec2ts(0)

        self.model.update_state(
            self.current_playlist, {
                'episodes': {
                    vid.title: {
                        'current_timestamp': new_ts
                    }
                }
            })

        self.player.setup(reload_playlist=False)

    def _init_player(self) -> None:
        self.player = PlayerQueue(self)
        self.player.setup(reset_position=True)

    def save_state(self) -> None:
        if self.player is not None:
            logger.info('Explicit state save')
            assert self.current_playlist is not None

            # update current video
            if self.player.current_vid is not None:
                assert self.player.ts is not None

                self.model.update_state(
                    self.current_playlist, {
                        'current': {
                            'title': self.player.current_vid.title,
                            'timestamp': sec2ts(self.player.ts)
                        },
                        'episodes': {
                            self.player.current_vid.title: {
                                'current_timestamp': sec2ts(self.player.ts)
                            }
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

        assert self.view.widget is not None, 'Widget has not been assembled'
        self.view.widget.update_info_box(txt)

    def send_msg(self, msg: str) -> None:
        assert self.view.widget is not None, 'Widget has not been assembled'
        self.view.widget.update_info_text(msg)

    def update_views(self) -> None:
        if not self.loop.screen.started:
            return None

        self.loop.draw_screen()

class PlayerQueue:
    def __init__(self, controller: Controller) -> None:
        self.controller = controller
        self.controller.player_backend.setup(
            self.handle_mpv_pos, self.handle_mpv_event,
            disable_video=not self.controller.config['show_video'])

        if self.controller.current_playlist is None:
            raise RuntimeError('Current playlist is not set')
        self.id = self.controller.model.get_playlist_info(
            self.controller.current_playlist)['id']

        self.playlist = None  # type: Optional['Playlist']
        self.current_vid = None  # type: Optional['Video']
        self.ts = None  # type: Optional[int]
        self.item_list = None  # type: Optional[List[str]]

    def setup(
        self,
        reload_playlist: bool = True, reset_position: bool = False
    ) -> None:
        def tmp() -> None:
            if reload_playlist:
                self.controller.send_msg('Loading...')

                plugin_name, self.playlist = load_playlist(self.id)
                self.controller.send_msg(
                    f'Loaded playlist with {plugin_name}')
            else:
                assert self.playlist is not None, \
                    'Playlist has not been loaded'

            state = self.controller.model._load_state()
            playlist_state = state[self.controller.current_playlist]

            v = self.controller.view.widget
            assert v is not None, 'Widget has not been assembled'

            # adjust video title display
            total_video_ts = 0
            self.item_list = []
            cols, _ = self.controller.loop.screen.get_cols_rows()
            for vid in self.playlist:
                vid_tit = vid.title
                vid_len = vid.duration

                if vid_tit in playlist_state['episodes']:
                    vid_info = playlist_state['episodes'][vid_tit]
                    vid_ts = ts2sec(vid_info['current_timestamp'])
                else:
                    vid_ts = 0
                total_video_ts += vid_ts
                vid_perc = round((vid_ts / vid_len) * 100) \
                    if vid_len > 0 else 0

                vid_tit = textwrap.shorten(vid_tit, cols-20)
                spaces = ' ' * (cols - len(vid_tit) - 19)
                cur = f'{vid_tit}{spaces} {sec2ts(vid_len):<10}{vid_perc:>3}%'
                self.item_list.append(cur)

            v.set_items(self.item_list)

            # set episode-view title
            total_video_perc = round(
                (total_video_ts / self.playlist.duration) * 100) \
                if self.playlist.duration > 0 else 0
            pl_tit = textwrap.shorten(self.playlist.title, cols-20)
            spaces = ' ' * (cols - len(pl_tit) - 17)
            v.set_title(
                f'{pl_tit}{spaces} '
                f'{sec2ts(self.playlist.duration):<10}'
                f'{total_video_perc:>3}%')
            self.controller.assemble_info_box()

            # set list focus to video watched was played last
            if reset_position:
                assert self.controller.current_playlist is not None
                _cur = self.controller.model.get_current_video(
                    self.controller.current_playlist)
                if _cur is not None:
                    idx, _ = self.playlist.get_video_by_title(_cur['title'])
                    v.vid_list.set_focus(idx)
                    self.controller.update_views()

        t = threading.Thread(target=tmp)
        t.start()

    def handle_mpv_pos(self, pos: float) -> None:
        assert self.current_vid is not None

        if pos is not None:
            self.ts = int(pos)
            assert self.ts is not None

            self.controller.send_msg(
                f'Playing "{self.current_vid.title}" ({sec2ts(self.ts)})')

    def handle_mpv_event(self, ev: PlayerEvent) -> None:
        if ev is PlayerEvent.VIDEO_OVER:
            self.onVideoEnd(play_next=True)
        elif ev is PlayerEvent.VIDEO_QUIT:
            self.controller.send_msg('Waiting for input')
            self.onVideoEnd()

    def onVideoEnd(self, play_next: bool = False) -> None:
        self.controller.assemble_info_box()

        if play_next:
            self.play_next_video()

        self.setup(reload_playlist=False)

    def play_video(self, vid: 'Video', start_pos: int = 0) -> None:
        self.controller.save_state()
        self.ts = start_pos
        self.current_vid = vid

        self.controller.player_backend.play_video(
            vid.get_file_stream(), vid.title,
            start=start_pos)

    def play_next_video(self) -> None:
        if self.current_vid is None:
            self.controller.send_msg('No video selected, cannot play next')
            return

        vid = self._get_video_relative(1)
        if vid is None:
            self.controller.send_msg('Reached end of playlist')
        else:
            self.play_video(vid)

    def play_previous_video(self) -> None:
        if self.current_vid is None:
            self.controller.send_msg('No video selected, cannot play previous')
            return

        vid = self._get_video_relative(-1)
        if vid is None:
            self.controller.send_msg('Reached end of playlist')
        else:
            self.play_video(vid)

    def _get_video_relative(self, idx_shift: int) -> Optional['Video']:
        assert self.playlist is not None
        assert self.current_vid is not None

        idx, _ = self.playlist.get_video_by_title(self.current_vid.title)
        if idx is None:
            raise RuntimeError(
                f'Could not find video "{self.current_vid.title}"')

        next_idx = idx + idx_shift

        if next_idx < len(self.playlist):
            return self.playlist[next_idx]
        else:
            return None
