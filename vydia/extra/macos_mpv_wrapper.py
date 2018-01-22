import sys
import threading
import multiprocessing

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QApplication


class DummyWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = QWidget(self)
        self.setCentralWidget(self.container)
        self.container.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.container.setAttribute(Qt.WA_NativeWindow)

        self.window_id = str(int(self.container.winId()))

class MPVProxy:
    def __init__(self, *args, **kwargs):
        self.mpv_args = args
        self.mpv_kwargs = kwargs

        # dummy functions
        self.time_handler = lambda t, v: (t, v)

        # setup MPV
        self.pipe = multiprocessing.Pipe()
        multiprocessing.Process(
            target=self._run, args=(self.pipe,)).start()

        # poll pipe (handle data incoming from mpv-process)
        def handle_pipe():
            output_p, input_p = self.pipe
            while True:
                try:
                    type_, val = input_p.recv()

                    if type_ == 'time-pos':
                        self.time_handler(type_, val)
                    else:
                        raise RuntimeError(f'Invalid property-type "{type_}"')
                except EOFError:
                    break
        threading.Thread(target=handle_pipe).start()

    def __getattr__(self, cmd):
        def wrapper(*args, **kwargs):
            if cmd == 'observe_property':  # handle unpickle-able lambdas
                type_, func = args
                if type_ == 'time-pos':
                    self.time_handler = func
                else:
                    raise RuntimeError(f'Invalid property-type "{type_}"')
            else:
                output_p, input_p = self.pipe
                try:
                    input_p.send((cmd, args, kwargs))
                except AttributeError as e:
                    print(f'Failed to send "{e}"')
        return wrapper

    def _run(self, pipe):
        # setup QT window
        app = QApplication([])
        win = DummyWindow()
        win.show()

        # initialize MPV
        import mpv
        player = mpv.MPV(*self.mpv_args, **self.mpv_kwargs)
        mpv._mpv_set_option_string(
            player.handle,
            'wid'.encode('utf-8'), win.window_id.encode('utf-8'))

        # send time-position to parent process
        def handle_time(prop_name, pos):
            output_p, input_p = pipe
            output_p.send((prop_name, pos))
        player.observe_property('time-pos', handle_time)

        # poll pipe (handle data sent to mpv-process)
        def handle_pipe():
            output_p, input_p = pipe
            while True:
                try:
                    msg = output_p.recv()
                    cmd, args, kwargs = msg

                    try:
                        func = getattr(player, cmd)
                    except AttributeError:
                        print(f'Invalid command "{cmd}"')
                        continue

                    func(*args, **kwargs)
                except EOFError:
                    break
        threading.Thread(target=handle_pipe).start()

        # run QT main-loop
        sys.exit(app.exec_())


def main():
    import time

    mp = MPVProxy(
        input_default_bindings=True,
        input_vo_keyboard=True,
        ytdl=True)

    print('Start')
    time.sleep(2)
    mp.non_existing_function()
    time.sleep(2)
    mp.play('test.webm')
    print('End')

if __name__ == '__main__':
    main()
