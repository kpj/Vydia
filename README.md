# Vydia

A modularized video player written in Python.

## Installation

```bash
$ pip install vydia
```

## Parameters and Commands

```bash
$ vydia --help
Usage: vydia [OPTIONS] COMMAND [ARGS]...

Options:
  --video / --no-video  Suppress mpv video output.
  --help                Show this message and exit.

Commands:
  add_playlist
```

Additionally, an internal commandline can be summoned by typing `:`.
The following commands are supported (in the correct context):
* `reload`: reload playlist using plugin
* `reverse`: reverse episode order
* `shuffle`: shuffle episode order
* `next`: play next video (`[>]`)
* `previous`: play previous video (`[<]`)
* `continue`: continue playback from last save (`[c]`)
* `quit`: quit Vydia (`[q]`)

## Plugins

* Filesystem
* Youtube
