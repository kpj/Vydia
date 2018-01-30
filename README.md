# Vydia

[![PyPI](https://img.shields.io/pypi/v/vydia.svg?style=flat)](https://pypi.python.org/pypi/vydia)
[![Build Status](https://img.shields.io/travis/kpj/Vydia.svg?style=flat)](https://travis-ci.org/kpj/Vydia)

A modularized video player written in Python (supporting AirPlay).

![Vydia-gif](docs/vydia.gif)


## Installation

```bash
$ pip install vydia
```

## Usage

Simply call `vydia` without arguments to launch the TUI:

```bash
$ vydia
```

## Parameters and Commands

```bash
$ vydia --help
Usage: vydia [OPTIONS] COMMAND [ARGS]...

Options:
  --video / --no-video  Suppress mpv video output.
  --airplay TEXT        Use airplay server if specified (format: "<ip>:<port>").
  --help                Show this message and exit.

Commands:
  add_playlist          Add new playlist by id.
  list_airplay_devices  List available airplay devices.
```

Additionally, an internal commandline can be summoned by typing `:`.
The following commands are supported (in the correct context):
* Playlist View:
  * `add <playlist id>`: add given playlist
  * `delete`: delete currently selected playlist
  * `quit`: quit Vydia (`[q]`)
* Episode View:
  * `pause`: toggle pause in running episode (`<space>`)
  * `reload`: reload playlist using plugin
  * `reverse`: reverse episode order
  * `shuffle`: shuffle episode order
  * `next`: play next video (`[>]`)
  * `previous`: play previous video (`[<]`)
  * `continue`: continue playback from last save (`[c]`)
  * `quit`: quit Vydia (`[q]`)

Furthermore, the following shortcuts exist:
* Episode View:
  * `w`: (un)mark currently selected video as watched

## Plugins

* Filesystem
* Youtube
