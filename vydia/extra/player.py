import threading

from typing import Any, Callable

import mpv


class Player(object):
    def __init__(
        self,
        time_callback: Callable[[str, float], None],
        event_callback: Callable[[Any], None],
        disable_video: bool = False
    ) -> None:
        optional_opts = {}
        if disable_video:
            optional_opts['vo'] = 'null'

        self.mpv = mpv.MPV(
            'force-window',
            input_default_bindings=True, input_vo_keyboard=True,
            ytdl=True, **optional_opts)

        self.mpv.observe_property('time-pos', time_callback)
        self.mpv.register_event_callback(event_callback)

        stop_keys = (
            'q', 'Q', 'POWER', 'STOP', 'CLOSE_WIN',
            'Ctrl+c', 'AR_PLAY_HOLD', 'AR_CENTER_HOLD')
        for key in stop_keys:
            self.mpv.register_key_binding(key, 'stop')

    def queue_video(self, vid: str) -> None:
        plc = int(self.mpv._get_property('playlist-count'))
        mode = 'replace' if plc == 0 else 'append-play'
        self.mpv.loadfile(vid, mode=mode)

    def play_video(self, title: str, vid: str, start: int = 0) -> None:
        #self.mpv.command('stop')
        self.mpv.playlist_clear()
        self.mpv['title'] = title
        self.mpv.loadfile(vid, start=start)

    def join(self) -> None:
        """ Wait for playlist to finish
        """
        self.mpv.wait_for_property('filename', lambda x: x is None)

    def stop(self) -> None:
        """ Close player
        """
        self.mpv.terminate()


if __name__ == '__main__':
    def _print_time(prop_name: str, time: float) -> None:
        if time is not None:
            print('[\033[93m{:06.2f}\033[0m]'.format(time), flush=True)

    def _print_event(ev: Any) -> None:
        print(ev)

    pl = Player(_print_time, _print_event)

    #pl.play_video('..')
    #pl.queue_video('..')

    pl.join()
