"""
Main interface
"""

from typing import Any

import click

from .core.controller import Controller
from .core.model import Model


@click.group(invoke_without_command=True)
@click.option(
    '--video/--no-video', default=True,
    help='Suppress mpv video output.')
@click.pass_context
def main(ctx: Any, video: bool) -> None:
    config = {
        'show_video': video
    }

    if ctx.invoked_subcommand is None:
        with Controller(config) as c:
            c.main()

@main.command()
@click.argument('playlist')
def add_playlist(playlist: str) -> None:
    title, plugin = Model().add_new_playlist(playlist)
    print(f'Added "{title}" using {plugin}')

if __name__ == '__main__':
    main()
