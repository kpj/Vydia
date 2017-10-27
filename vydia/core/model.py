import os
import json
import collections

from pathlib import Path
from appdirs import AppDirs

from typing import Any, Union, Optional, Iterable, Dict, List

from ..extra.utils import nested_dict_update


class Model:
    def __init__(
        self,
        state_fname: Optional[Path] = None,
        log_fname: Optional[Path] = None
    ) -> None:
        self.adirs = AppDirs('vydia', 'kpj')

        self.STATE_FILE: Path = state_fname \
            or Path(self.adirs.user_data_dir) / 'state.json'
        self.LOG_FILE: Path = log_fname \
            or Path(self.adirs.user_log_dir) / 'log.txt'

        self._ensure_dir(str(self.LOG_FILE))

    def get_playlist_list(self) -> Iterable[str]:
        return sorted(self._load_state().keys())

    def get_playlist_info(self, pid: str) -> Dict[str, str]:
        cur = self._load_state()[pid]
        cur.update({'name': pid})
        return cur

    def get_current_video(self, pid: str) -> Dict[str, str]:
        _state = self._load_state()
        return _state[pid].get('current', None)

    def update_state(
        self,
        pid: str, data: Dict[str, str]
    ) -> None:
        _state = self._load_state()

        if pid in _state:
            _state[pid] = nested_dict_update(_state[pid], data)
        else:
            _state[pid] = data

        self._save_state(_state)

    def _ensure_dir(self, fname: str) -> None:
        """ Make sure that directory exists
        """
        dir_ = os.path.dirname(fname)
        if not os.path.isdir(dir_):
            os.makedirs(dir_)

    def _load_state(self, fn: Optional[str] = None) -> Dict[Any, Any]:
        """ Load state
        """
        fname = str(fn or self.STATE_FILE)
        self._ensure_dir(fname)

        if not os.path.isfile(fname):
            res: Dict[Any, Any] = {}
        else:
            with open(fname) as fd:
                res = json.load(fd)

        return collections.defaultdict(dict, res)

    def _save_state(
        self,
        state: Dict[Any, Any], fn: Optional[str] = None
    ) -> None:
        fname = str(fn or self.STATE_FILE)
        self._ensure_dir(fname)

        with open(fname, 'w') as fd:
            json.dump(state, fd)
