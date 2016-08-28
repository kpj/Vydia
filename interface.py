"""
Setup user interface
"""

import urwid


class App(object):
    def __init__(self, title, items, onSelect=None, onKey=None):
        self.onSelect = onSelect
        self.onKey = onKey
        self.loop = None

        self.info_box = None
        self.info_bar = None

        self.init_app(title, items)

    def init_app(self, title, items):
        body = []
        for it in items:
            button = urwid.Button(it)
            urwid.connect_signal(button, 'click', self.select, it)
            body.append(
                urwid.AttrMap(button, None, focus_map='reversed'))

        vid_list = urwid.ListBox(urwid.SimpleFocusListWalker(body))
        self.info_box = urwid.LineBox(urwid.Text('INFO'))

        main = urwid.Frame(vid_list, footer=self.info_box)
        self.info_bar = urwid.Text('[Help] q: quit, c: continue last video')

        self.loop = urwid.MainLoop(
            urwid.Frame(main,
                header=urwid.Text(title),
                footer=self.info_bar),
            palette=[('reversed', 'standout', '')],
            unhandled_input=self.unhandled_input)

    def run(self):
        if self.loop is None:
            print('Must initialize app first, doing so now')
            self.init_app()

        self.loop.run()

    def select(self, button, choice):
        if not self.onSelect is None:
            self.onSelect(choice)

    def unhandled_input(self, key):
        if key in ('Q', 'q', 'esc'):
            raise urwid.ExitMainLoop()

        if not self.onKey is None:
            self.onKey(key)

def main():
    app = App('hello :-)', ['hey', 'hi'])
    app.run()

if __name__ == '__main__':
    main()
