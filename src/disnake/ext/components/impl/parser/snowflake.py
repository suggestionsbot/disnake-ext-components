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
class SnowflakeParser(parser_base.Parser[disnake.abc.Snowflake]):

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(self, argument: str) -> disnake.Object:

        return disnake.Object(self.int_parser.loads(argument))

    def dumps(self, argument: disnake.abc.Snowflake) -> str:

    def loads(self, argument: str) -> disnake.Object:  # noqa: D102
        return self.int_parser.dumps(argument.id)


ObjectParser = SnowflakeParser  # TODO: Remove.
