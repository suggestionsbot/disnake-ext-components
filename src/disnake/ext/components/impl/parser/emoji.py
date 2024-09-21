"""Parser implementations for disnake emoji types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import helpers

__all__: typing.Sequence[str] = (
    "GetEmojiParser",
    "EmojiParser",
    "PartialEmojiParser",
    "GetStickerParser",
    "StickerParser",
)


# GET_ONLY


@parser_base.register_parser_for(disnake.Emoji)
class GetEmojiParser(parser_base.SourcedParser[disnake.Emoji]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAware
    ) -> disnake.Emoji:
        # <<docstring inherited from parser_api.Parser>>

        emoji = source.bot.get_emoji(self.int_parser.loads(argument))

        if emoji is None:
            msg = f"Could not find an emoji with id {argument!r}."
            raise LookupError(msg)

        return emoji

    def dumps(self, argument: disnake.Emoji) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Sticker)
class GetStickerParser(parser_base.SourcedParser[disnake.Sticker]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAware
    ) -> disnake.Sticker:
        # <<docstring inherited from parser_api.Parser>>

        sticker = source.bot.get_sticker(self.int_parser.loads(argument))

        if sticker is None:
            msg = f"Could not find an emoji with id {argument!r}."
            raise LookupError(msg)

        return sticker

    def dumps(self, argument: disnake.Sticker) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


# GET AND FETCH


@parser_base.register_parser_for(disnake.Emoji)
class EmojiParser(parser_base.SourcedParser[disnake.Emoji]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    async def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAndGuildAware
    ) -> disnake.Emoji:
        # <<docstring inherited from parser_api.Parser>>

        if source.guild is None:
            msg = (
                "Impossible to fetch an emoji from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)

        emoji_id = self.int_parser.loads(argument)
        return (
            source.bot.get_emoji(emoji_id)
            or await source.guild.fetch_emoji(emoji_id)
        )  # fmt: skip

    def dumps(self, argument: disnake.Emoji) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


# TODO: Maybe implement some way of *not* requiring ids for partial emoji
@parser_base.register_parser_for(disnake.PartialEmoji)
class PartialEmojiParser(parser_base.Parser[disnake.PartialEmoji]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(self, argument: str) -> disnake.PartialEmoji:  # noqa: D102
        return disnake.PartialEmoji.from_dict({"id": self.int_parser.loads(argument)})

    def dumps(self, argument: disnake.PartialEmoji) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>
        if not argument.id:
            msg = "PartialEmojiParser requires PartialEmoji.id to be set."
            raise ValueError(msg)

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Sticker)
class StickerParser(parser_base.SourcedParser[disnake.Sticker]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    async def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAndGuildAware
    ) -> disnake.Sticker:
        # <<docstring inherited from parser_api.Parser>>

        if source.guild is None:
            msg = (
                "Impossible to fetch a sticker from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)

        sticker_id = self.int_parser.loads(argument)
        return (
            source.bot.get_sticker(sticker_id)
            or await source.guild.fetch_sticker(sticker_id)
        )  # fmt: skip

    def dumps(self, argument: disnake.Sticker) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)
