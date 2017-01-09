"""
Setup user interface
"""

import urwid


class BaseView(object):
    def __init__(self, title, items, onSelect=None, onKey=None):
        self.onSelect = onSelect
        self.onKey = onKey
        self.loop = None

        self.title = title
        self.items = items

    def init_app(self):
        raise NotImplementedError

    def run(self):
        if self.loop is None:
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

class IntroScreen(BaseView):
    def __init__(self, title, items, onButton=None, onSelect=None, onKey=None):
        self.onButton_custom = onButton
        super().__init__(title, items, onSelect, onKey)

    def init_app(self):
        body = []
        for it in self.items:
            button = urwid.Button(it)
            urwid.connect_signal(button, 'click', self.select, it)
            body.append(
                urwid.AttrMap(button, None, focus_map='reversed'))

        self.main_list = urwid.SimpleFocusListWalker(body)
        item_list = urwid.ListBox(self.main_list)

        self.editor = urwid.Edit(
            caption='Add new playlist: ',
            edit_text='<id>')

        self.loop = urwid.MainLoop(
            urwid.Frame(item_list,
                header=urwid.Text(self.title),
                footer=urwid.Columns([
                    self.editor,
                    urwid.Button('Ok', on_press=self.onButton)
                ])),
            palette=[('reversed', 'standout', '')],
            unhandled_input=self.unhandled_input)

    def onButton(self, _):
        sel = self.editor.get_edit_text()
        cur = urwid.AttrMap(
            urwid.Button(sel),
            None, focus_map='reversed')
        self.main_list.append(cur)

        if not self.onButton_custom is None:
            self.onButton_custom(sel)

class App(BaseView):
    def __init__(self, title, items, onSelect=None, onKey=None):
        self.info_box = None
        self.info_bar = None

        super().__init__(title, items, onSelect, onKey)

    def init_app(self):
        body = []
        for it in self.items:
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
                header=urwid.Text(self.title),
                footer=self.info_bar),
            palette=[('reversed', 'standout', '')],
            unhandled_input=self.unhandled_input)

def main():
    intro = IntroScreen('Intro', ['foo', 'bar'])
    intro.run()

    app = App('hello :-)', ['hey', 'hi'])
    app.run()

if __name__ == '__main__':
    main()
