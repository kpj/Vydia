import logging
from abc import ABC, abstractmethod

import urwid

#from .controller import Controller # TODO: fix typing import


class View(urwid.WidgetWrap):
    def __init__(self, controller: 'Controller') -> None:
        self.controller = controller
        self.widget = None

        urwid.WidgetWrap.__init__(self, self.intro_screen())

    def _activate_widget(self, w) -> None:
        self.controller.input_callback = w.handle_input
        self.controller.loop.widget = w.build()
        self.widget = w

    def intro_screen(self) -> urwid.Widget:
        w = urwid.Filler(urwid.Text('Loading'), 'top')
        return w

    def show_playlist_overview(self) -> None:
        w = PlaylistOverview(self.controller)
        self._activate_widget(w)

    def show_episode_overview(self) -> None:
        w = EpisodeOverview(self.controller)
        self._activate_widget(w)


class BaseView(ABC):
    def __init__(self, title, items) -> None:
        self.title = title
        self.items = items

    @abstractmethod
    def build(self):
        pass

    def handle_mouse(self, button, choice):
        pass

    def handle_input(self, key):
        pass


class PlaylistOverview(BaseView):
    def __init__(self, controller):
        self.controller = controller

        super().__init__(
            'Existing playlists', self.controller.get_playlist_list())

    def handle_mouse(self, button, choice):
        self.controller.on_playlist_selected(choice)

    def build(self):
        body = []
        for it in self.items:
            button = urwid.Button(it)
            urwid.connect_signal(button, 'click', self.handle_mouse, it)
            body.append(
                urwid.AttrMap(button, None, focus_map='reversed'))

        self.main_list = urwid.SimpleFocusListWalker(body)
        item_list = urwid.ListBox(self.main_list)

        return urwid.Frame(item_list, header=urwid.Text(self.title))


class EpisodeOverview(BaseView):
    def __init__(self, controller):
        self.controller = controller

        self.info_box = None
        self.info_bar = None
        self.title_widget = None

        self.info = self.controller.get_current_playlist_info()

        super().__init__('Loading...', [])

    def build(self):
        self.vid_list = urwid.SimpleFocusListWalker([])
        self.info_box = urwid.LineBox(urwid.Text('Nothing to show...'))

        main = urwid.Frame(
            urwid.ListBox(self.vid_list), footer=self.info_box)
        self.info_bar = urwid.Text('[Help] q: quit, c: continue last video')

        self.title_widget = urwid.Text(self.title)

        return urwid.Frame(main,
            header=self.title_widget, footer=self.info_bar)

    def update_info_text(self, txt):
        self.info_bar.set_text(txt)
        self.controller.loop.draw_screen()

    def update_info_box(self, txt):
        self.info_box.base_widget.set_text(txt)
        self.controller.loop.draw_screen()

    def handle_mouse(self, button, choice):
        self.controller.on_video_selected(choice)

    def handle_input(self, key) -> None:
        if isinstance(key, str) and key.lower() == 'c':
            self.controller.continue_playback()
        else:
            logging.info(f'Unknown key "{key}"')

    def set_title(self, title):
        self.title = title
        self.title_widget.set_text(self.title)

        self.controller.loop.draw_screen()

    def set_items(self, items):
        self.items = items
        for it in self.items:
            button = urwid.Button(it)
            urwid.connect_signal(button, 'click', self.handle_mouse, it)
            self.vid_list.append(
                urwid.AttrMap(button, None, focus_map='reversed'))

        self.controller.loop.draw_screen()