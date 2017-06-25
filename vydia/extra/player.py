import threading

import mpv


class Player(object):
    def __init__(self, time_callback, event_callback):
        self.mpv = mpv.MPV(
            'force-window',
            input_default_bindings=True, input_vo_keyboard=True,
            ytdl=True)

        self.mpv.observe_property('time-pos', time_callback)
        self.mpv.register_event_callback(event_callback)

        for key in ('q', 'Q', 'POWER', 'STOP', 'CLOSE_WIN', 'Ctrl+c', 'AR_PLAY_HOLD', 'AR_CENTER_HOLD'):
            self.mpv.register_key_binding(key, 'stop')

    def queue_video(self, vid):
        plc = int(self.mpv._get_property('playlist-count'))
        mode = 'replace' if plc == 0 else 'append-play'
        self.mpv.loadfile(vid, mode=mode)

    def play_video(self, vid, start=0):
        #self.mpv.command('stop')
        self.mpv.playlist_clear()
        self.mpv.loadfile(vid, start=start)

    def join(self):
        """ Wait for playlist to finish
        """
        self.mpv.wait_for_property('filename', lambda x: x is None)


if __name__ == '__main__':
    def _print_time(time):
        if time is not None:
            print('[\033[93m{:06.2f}\033[0m]'.format(time), flush=True)

    def _print_event(ev):
        print(ev)

    pl = Player(_print_time, _print_event)

    #pl.play_video('..')
    #pl.queue_video('..')

    pl.join()
