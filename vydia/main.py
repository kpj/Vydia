"""
Main interface
"""

from typing import Any

import click

from .extra.player import BasePlayer


def get_player(airplay: str) -> BasePlayer:
    """ Yield local of airplay Player, depending on given specification
    """
    player: BasePlayer

    if airplay:
        host, port = airplay.split(':')

        from .extra.player import AirPlayer
        player = AirPlayer(host, int(port))
    else:
        from .extra.player import LocalPlayer
        player = LocalPlayer()

    return player

@click.group(invoke_without_command=True)
@click.option(
    '--video/--no-video', default=True,
    help='Suppress mpv video output.')
@click.option(
    '--airplay', default='',
    help='Use airplay server if specified (format: "<ip>:<port>").')
@click.pass_context
def main(ctx: Any, video: bool, airplay: str) -> None:
    config = {
        'show_video': video
    }

    if ctx.invoked_subcommand is None:
        from .core.controller import Controller
        with Controller(get_player(airplay), config) as c:
            c.main()

@main.command(help='Add new playlist by id.')
@click.argument('playlist')
def add_playlist(playlist: str) -> None:
    from .core.model import Model
    result = Model().add_new_playlist(playlist)
    if result is None:
        print('Playlist could not be added')
        exit(-1)

    title, plugin = result
    print(f'Added "{title}" using {plugin}')

@main.command(help='List available airplay devices.')
def list_airplay_devices() -> None:
    from airplay import AirPlay
    for i, ap in enumerate(AirPlay.find(fast=False)):
        info = ap.server_info()
        print(f'#{i+1}: {ap.host}:{ap.port} ({info["model"]})')

if __name__ == '__main__':
    main()
