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

        # setup MPV
        self.pipe = multiprocessing.Pipe()
        multiprocessing.Process(
            target=self._run, args=(self.pipe,)).start()

    def __getattr__(self, cmd):
        def wrapper(*args, **kwargs):
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

        # poll pipe
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
