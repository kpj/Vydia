"""
Plugins for video backends
"""

import os
import random
import collections
from abc import ABC, abstractmethod

from typing import Any, List, Tuple, Optional, Type, Callable  # noqa: F401

import pafy

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

from .utils import get_video_duration


VideoData = collections.namedtuple(
    'VideoData', ['title', 'duration', 'get_file_stream', 'get_info']
)  # type: Tuple[str, int, Callable[[], str], Callable[[], str]]


class Video(object):
    @classmethod
    def from_pafy(cls: Type['Video'], obj: Any) -> 'Video':
        def format_info() -> str:
            return f'Title: {obj.title}\n' + \
                f'Author: {obj.author}\n' + \
                f'Published: {obj.published}\n' + \
                f'Description: {obj.description}'

        return cls(VideoData(
            title=obj.title,
            duration=obj.length,
            get_file_stream=lambda: obj.getbest().url,
            get_info=format_info
        ))

    @classmethod
    def from_filepath(cls: Type['Video'], path: str) -> 'Video':
        def format_info() -> str:
            with createParser(path) as parser:
                try:
                    metadata = extractMetadata(parser)
                except Exception as err:
                    return f'No video-data found ({err})'
            return '\n'.join(metadata.exportPlaintext())

        return cls(VideoData(
            title=os.path.basename(path),
            duration=get_video_duration(path),
            get_file_stream=lambda: path,
            get_info=format_info
        ))

    def __init__(self, obj: VideoData) -> None:
        self._obj = obj

    def __getattr__(self, key: str) -> Any:
        return self._obj._asdict()[key]


class Playlist(List['Video']):
    def __init__(self) -> None:
        self._id = None
        self._title = ''
        super().__init__()

    @property
    def id(self) -> str:
        if self._id is None:
            raise RuntimeError('Id not yet set.')

        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def duration(self) -> int:
        return sum([v.duration for v in self])

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


class BasePlugin(ABC):
    @abstractmethod
    def extract_playlist(self, url: str) -> Optional[Playlist]:
        """ Return playlist object
            None if invalid url
        """


class FilesystemPlugin(BasePlugin):
    def extract_playlist(self, url: str) -> Optional[Playlist]:
        url = os.path.abspath(url)
        if not os.path.exists(url):
            return None

        pl = Playlist()
        pl._id = url
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
        pl._id = url

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
