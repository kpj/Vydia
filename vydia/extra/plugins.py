"""
Plugins for video backends
"""

from abc import ABCMeta, abstractmethod, abstractproperty

import pafy


class Video(object):
    @classmethod
    def from_pafy(cls, obj):
        return cls(obj)

    def __init__(self, obj):
        self._obj = obj

    @property
    def title(self):
        return self._obj.title

    @property
    def duration(self):
        return self._obj.length

    @property
    def stream(self):
        return self._obj.getbest().url

class Playlist(object):
    def __init__(self):
        self._title = ''
        self._videos = []

        self.vid_idx = 0 # TODO: handle in self.__iter__

    @property
    def title(self):
        return self._title

    def __iter__(self):
        self.vid_idx = 0
        return self

    def __next__(self):
        if self.vid_idx >= len(self._videos):
            raise StopIteration
        else:
            self.vid_idx += 1
            return self._videos[self.vid_idx-1]

    def get_video_by_title(self, title):
        for i, vid in enumerate(self._videos):
            if vid.title == title:
                return i, vid
        return None, None

class BasePlugin(metaclass=ABCMeta):
    @abstractmethod
    def extract_playlist(self, url):
        """ Return playlist object
            None if invalid url
        """
        return

class YoutubePlugin(BasePlugin):
    def extract_playlist(self, url):
        try:
            res = pafy.get_playlist2(url)
        except ValueError:
            return None
        pl = Playlist()

        pl._title = res.title
        for vid in res:
            pl._videos.append(Video.from_pafy(vid))

        return pl

#    def handle_video(self, vid):
#        video = pafy.new(url, basic=False)
#        print(video.title, video.duration)
#
#        best = video.getbest()
#        print(best.url, best.resolution, best.get_filesize())
#        #best.download(filepath='/tmp/', quiet=False)
