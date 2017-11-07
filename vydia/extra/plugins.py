"""
Plugins for video backends
"""

import os
import random
import collections
from abc import ABCMeta, abstractmethod, abstractproperty

from typing import Any, List, Tuple, Optional, Type, Callable

import pafy

from .utils import get_video_duration


VideoData = collections.namedtuple(
    'VideoData', ['title', 'duration', 'get_file_stream']
)  # type: Tuple[str, int, Callable[[], str]]

class Video(object):
    @classmethod
    def from_pafy(cls: Type['Video'], obj: Any) -> 'Video':
        return cls(VideoData(
            title=obj.title,
            duration=obj.length,
            get_file_stream=lambda: obj.getbest().url
        ))

    @classmethod
    def from_filepath(cls: Type['Video'], path: str) -> 'Video':
        return cls(VideoData(
            title=os.path.basename(path),
            duration=get_video_duration(path),
            get_file_stream=lambda: path
        ))

    def __init__(self, obj: VideoData) -> None:
        self._obj = obj

    def __getattr__(self, key: str) -> Any:
        return self._obj._asdict()[key]

class Playlist(List['Video']):
    def __init__(self) -> None:
        self._title = ''
        super().__init__()

    @property
    def title(self) -> str:
        return self._title

    def reverse(self) -> None:
        tmp = self[:]
        self.clear()

        for v in reversed(tmp):
            self.append(v)

    def shuffle(self) -> None:
        tmp = self[:]
        self.clear()

        random.shuffle(tmp)
        for v in tmp:
            self.append(v)

    def get_video_by_title(
        self, title: str
    ) -> Tuple[Optional[int], Optional[Video]]:
        for i, vid in enumerate(self):
            if vid.title == title:
                return i, vid
        return None, None

class BasePlugin(metaclass=ABCMeta):
    @abstractmethod
    def extract_playlist(self, url: str) -> Optional[Playlist]:
        """ Return playlist object
            None if invalid url
        """

class FilesystemPlugin(BasePlugin):
    def extract_playlist(self, url: str) -> Optional[Playlist]:
        if not os.path.exists(url):
            return None

        pl = Playlist()
        pl._title = url

        paths = []
        for entry in os.scandir(url):
            if entry.is_dir():
                print(f'Skipping {entry.path}')
                continue
            paths.append(entry.path)

        for fp in sorted(paths):
            pl.append(Video.from_filepath(fp))

        return pl

class YoutubePlugin(BasePlugin):
    def extract_playlist(self, url: str) -> Optional[Playlist]:
        try:
            res = pafy.get_playlist2(url)
        except ValueError:
            return None
        pl = Playlist()

        pl._title = res.title
        for vid in res:
            pl.append(Video.from_pafy(vid))

        return pl

#    def handle_video(self, vid):
#        video = pafy.new(url, basic=False)
#        print(video.title, video.duration)
#
#        best = video.getbest()
#        print(best.url, best.resolution, best.get_filesize())
#        #best.download(filepath='/tmp/', quiet=False)
