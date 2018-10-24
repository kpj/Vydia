"""
Main interface
"""

from typing import Any

import click

from .extra.player import BasePlayer


def get_player(remote: str) -> BasePlayer:
    """ Yield local or airplay Player, depending on given specification
    """
    player: BasePlayer
    server_type, url = (remote.split('::')
                        if len(remote) > 0 else ('local', None))

    if server_type == 'local':
        from .extra.player import LocalPlayer
        player = LocalPlayer()
    elif server_type.lower() == 'airplay':
        host, port = url.split(':')

        from .extra.player import AirPlayer
        player = AirPlayer(host, int(port))
    elif server_type.lower() == 'dlna':
        from .extra.player import DLNAPlayer
        player = DLNAPlayer(url)
    else:
        raise RuntimeError(f'Invalid player specification "{remote}"')

    return player


@click.group(invoke_without_command=True)
@click.option(
    '--video/--no-video', default=True,
    help='Suppress mpv video output.')
@click.option(
    '--titles/--no-titles', default=True,
    help='Display title at beginning of each video.')
@click.option(
    '--remote', default='',
    help='Use remote server if specified '
         '(format: "airplay::<ip>:<port>", "dlna::<url>").')
@click.pass_context
def main(ctx: Any, video: bool, titles: bool, remote: str) -> None:
    config = {
        'show_video': video,
        'show_titles': titles
    }

    if ctx.invoked_subcommand is None:
        from .core.controller import Controller
        with Controller(get_player(remote), config) as c:
            c.main()


@main.command(help='Add new playlist by id.')
@click.argument('playlist', nargs=-1, required=True)
def add_playlist(playlist: str) -> None:
    from .core.model import Model

    for pl in playlist:
        result = Model().add_new_playlist(pl)
        if result is None:
            print(f'Playlist "{pl}" could not be added')
        else:
            title, plugin = result
            print(f'Added "{title}" using {plugin}')


@main.command(help='List available airplay devices.')
def list_airplay_devices() -> None:
    from airplay import AirPlay
    for i, ap in enumerate(AirPlay.find(fast=False)):
        info = ap.server_info()
        print(f'#{i+1}: {ap.host}:{ap.port} ({info["model"]})')


@main.command(help='List available DLNA devices.')
def list_dlna_devices() -> None:
    from nanodlna import devices
    for i, dev in enumerate(devices.get_devices()):
        print(f'#{i+1}: {dev["friendly_name"]} ({dev["location"]})')


if __name__ == '__main__':
    main()
