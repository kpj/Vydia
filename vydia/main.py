"""
Main interface
"""

from typing import Any

import click

from .core.controller import Controller
from .core.model import Model
from .extra.utils import load_playlist


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: Any) -> None:
    if ctx.invoked_subcommand is None:
        with Controller() as c:
            c.main()

@main.command()
@click.argument('playlist')
def add_playlist(playlist: str) -> None:
    try:
        plugin_name, pl = load_playlist(playlist)
    except ValueError:
        print(f'No plugin found for "{playlist}"')
        return

    Model().update_state(pl.title, {'id': playlist, 'episodes': {}})
    print(f'Added "{pl.title}" using {plugin_name}')

if __name__ == '__main__':
    main()
