import os
import sys
import enum
import time
import threading
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..core.controller import Controller  # noqa: F401


PlayerEvent = enum.Enum('PlayerEvent', 'VIDEO_OVER VIDEO_QUIT')


class BasePlayer(ABC):
    @abstractmethod
    def setup(
        self,
        time_callback: Callable[[float], None],
        event_callback: Callable[[PlayerEvent], None],
        disable_video: bool = False
    ) -> None:
        pass

    @abstractmethod
    def play_video(self, vid: str, title: str = '', start: int = 0) -> None:
        pass

    @abstractmethod
    def toggle_pause(self) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

    @abstractmethod
    def display_text(self, txt: str, duration: int = 1000) -> None:
        pass

    def set_controller(self, controller: 'Controller') -> None:
        self.controller = controller


class AirPlayer(BasePlayer):
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port

    def setup(
        self,
        time_callback: Callable[[float], None],
        event_callback: Callable[[PlayerEvent], None],
        disable_video: bool = False
    ) -> None:
        self.time_callback = time_callback
        self.event_callback = event_callback

        if disable_video:
            raise RuntimeError('Disabling video not supported with Airplay.')

        from airplay import AirPlay
        self.ap = AirPlay(self.ip, self.port)

        threading.Thread(
            target=self._handle_events, daemon=True).start()
        threading.Thread(
            target=self._check_video_position, daemon=True).start()

    def _handle_events(self) -> None:
        for event in self.ap.events():
            state = event['state']

            if state == 'stopped':
                if self.controller.player.ts is None:
                    return None
                assert self.controller.player is not None
                assert self.controller.player.current_vid is not None

                # AirPlay does not understand the difference between
                # force-stopping and gracefully ending a video when
                # it is over. Here, this is approximated by checking
                # how close we are to the video's end.
                # A difference of 5 seems to magically work out.
                MAGIC_END_MARKER = 5
                time2end = self.controller.player.current_vid.duration \
                    - self.controller.player.ts

                if time2end < MAGIC_END_MARKER:
                    self.event_callback(PlayerEvent.VIDEO_OVER)
                else:
                    self.event_callback(PlayerEvent.VIDEO_QUIT)

    def _check_video_position(self) -> None:
        while True:
            info = self.ap.playback_info()
            if info and 'position' in info:
                self.time_callback(info['position'])
            time.sleep(1)

    def _is_local_file(self, fname: str) -> bool:
        return os.path.exists(fname)

    def play_video(self, vid: str, title: str = '', start: int = 0) -> None:
        if self._is_local_file(vid):
            vid_url = self.ap.serve(os.path.abspath(vid))
        else:
            vid_url = vid

        # position must be fraction between 0 and 1
        assert self.controller.player is not None
        assert self.controller.player.current_vid is not None
        assert start <= self.controller.player.current_vid.duration
        start_frac = start / self.controller.player.current_vid.duration

        self.ap.play(vid_url, position=start_frac)

    def toggle_pause(self) -> None:
        info = self.ap.playback_info()
        if info['rate'] == 0:
            self.ap.rate(1)
        else:
            self.ap.rate(0)

    def shutdown(self) -> None:
        self.ap.stop()

    def display_text(self, txt: str, duration: int = 1000) -> None:
        """ Does not seem possible
        """
        pass


class LocalPlayer(BasePlayer):
    def setup(
        self,
        time_callback: Callable[[float], None],
        event_callback: Callable[[PlayerEvent], None],
        disable_video: bool = False
    ) -> None:
        self.time_callback = time_callback
        self.event_callback = event_callback

        optional_opts = {}
        if disable_video:
            optional_opts['vo'] = 'null'

        self.mpv = self._create_mpv_instance(**optional_opts)

        self.mpv.observe_property('time-pos', self._handle_mpv_pos)
        self.mpv.register_event_callback(self._handle_mpv_event)

        stop_keys = (
            'q', 'Q', 'POWER', 'STOP', 'CLOSE_WIN',
            'Ctrl+c', 'AR_PLAY_HOLD', 'AR_CENTER_HOLD')
        for key in stop_keys:
            self.mpv.register_key_binding(key, 'stop')

    def _create_mpv_instance(self, **optional_opts) -> 'mpv.MPV':
        if sys.platform == 'darwin':  # is macOS
            from .macos_mpv_wrapper import MPVProxy
            mpv = MPVProxy(
                input_default_bindings=True, input_vo_keyboard=True,
                ytdl=True,
                **optional_opts)
        else:
            import mpv
            mpv = mpv.MPV(
                'force-window',
                input_default_bindings=True,
                input_vo_keyboard=True,
                ytdl=True,
                **optional_opts)

        return mpv

    def _handle_mpv_pos(self, prop_name: str, pos: float) -> None:
        self.time_callback(pos)

    def _handle_mpv_event(self, ev: Any) -> None:
        if ev['event_id'] == 7:  # end-file
            reason = ev['event']['reason']
            if reason == 0:  # graceful shutdown
                self.event_callback(PlayerEvent.VIDEO_OVER)
            elif reason == 2:  # force quit
                self.event_callback(PlayerEvent.VIDEO_QUIT)

    def play_video(self, vid: str, title: str = '', start: int = 0) -> None:
        # self.mpv.command('stop')
        self.mpv.playlist_clear()
        self.mpv._set_property('title', title)
        # self.mpv['title'] = title
        self.mpv.loadfile(vid, start=start)

    def toggle_pause(self) -> None:
        self.mpv._set_property(
            'pause', not self.mpv.pause)
        # self.mpv.pause = not self.mpv.pause

    def shutdown(self) -> None:
        """ Close player
        """
        self.mpv.terminate()

    def display_text(self, txt: str, duration: int = 1000) -> None:
        self.mpv.show_text(txt, duration=duration)

    def queue_video(self, vid: str) -> None:
        plc = int(self.mpv._get_property('playlist-count'))
        mode = 'replace' if plc == 0 else 'append-play'
        self.mpv.loadfile(vid, mode=mode)

    def join(self) -> None:
        """ Wait for playlist to finish
        """
        self.mpv.wait_for_property('filename', lambda x: x is None)


if __name__ == '__main__':
    def _print_time(time: float) -> None:
        if time is not None:
            print('[\033[93m{:06.2f}\033[0m]'.format(time), flush=True)

    def _print_event(ev: PlayerEvent) -> None:
        print(ev)

    pl = LocalPlayer()
    pl.setup(_print_time, _print_event)

    # pl.play_video('..')
    # pl.queue_video('..')

    pl.join()
