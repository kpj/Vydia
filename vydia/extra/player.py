import threading
import enum
from abc import ABC, abstractmethod

from typing import Any, Callable


PlayerEvent = enum.Enum('PlayerEvent', 'VIDEO_OVER VIDEO_QUIT')

class BasePlayer(ABC):
    def __init__(
        self,
        time_callback: Callable[[float], None],
        event_callback: Callable[[PlayerEvent], None],
        disable_video: bool = False
    ) -> None:
        self.time_callback = time_callback
        self.event_callback = event_callback
        self.disable_video = disable_video

        self.setup()

    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def play_video(self, title: str, vid: str, start: int = 0) -> None:
        pass

    @abstractmethod
    def toggle_pause(self) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

class LocalPlayer(BasePlayer):
    def setup(self) -> None:
        optional_opts = {}
        if self.disable_video:
            optional_opts['vo'] = 'null'

        import mpv
        self.mpv = mpv.MPV(
            'force-window',
            input_default_bindings=True, input_vo_keyboard=True,
            ytdl=True, **optional_opts)

        self.mpv.observe_property('time-pos', self._handle_mpv_pos)
        self.mpv.register_event_callback(self._handle_mpv_event)

        stop_keys = (
            'q', 'Q', 'POWER', 'STOP', 'CLOSE_WIN',
            'Ctrl+c', 'AR_PLAY_HOLD', 'AR_CENTER_HOLD')
        for key in stop_keys:
            self.mpv.register_key_binding(key, 'stop')

    def _handle_mpv_pos(self, prop_name: str, pos: float) -> None:
        self.time_callback(pos)

    def _handle_mpv_event(self, ev: Any) -> None:
        if ev['event_id'] == 7:  # end-file
            reason = ev['event']['reason']
            if reason == 0:  # graceful shutdown
                self.event_callback(PlayerEvent.VIDEO_OVER)
            elif reason == 2:  # force quit
                self.event_callback(PlayerEvent.VIDEO_QUIT)

    def play_video(self, title: str, vid: str, start: int = 0) -> None:
        #self.mpv.command('stop')
        self.mpv.playlist_clear()
        self.mpv['title'] = title
        self.mpv.loadfile(vid, start=start)

    def toggle_pause(self) -> None:
        self.mpv.pause = not self.mpv.pause

    def shutdown(self) -> None:
        """ Close player
        """
        self.mpv.terminate()

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

    pl = LocalPlayer(_print_time, _print_event)

    #pl.play_video('..')
    #pl.queue_video('..')

    pl.join()
