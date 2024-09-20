"""Parser implementations for basic disnake snowflake types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from typing_extensions import deprecated

__all__: typing.Sequence[str] = ("SnowflakeParser",)


# TODO: Remove
@deprecated("replace all usage pls")
def snowflake_dumps(argument: disnake.abc.Snowflake) -> str:
    """Dump any kind of :class:`disnake.abc.Snowflake` to a string."""
    return str(argument.id)


@parser_base.register_parser_for(disnake.abc.Snowflake, disnake.Object)
class SnowflakeParser(parser_base.Parser[disnake.Object]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake_dumps

    def loads(self, argument: str) -> disnake.Object:  # noqa: D102
        return disnake.Object(int(argument))


ObjectParser = SnowflakeParser  # TODO: Remove.
