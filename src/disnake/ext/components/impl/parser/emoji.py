"""Parser implementations for disnake emoji types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import helpers, snowflake

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

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAware
    ) -> disnake.Emoji:
        # <<docstring inherited from parser_api.Parser>>

        emoji = source.bot.get_emoji(int(argument))

        if emoji is None:
            msg = f"Could not find an emoji with id {argument!r}."
            raise LookupError(msg)

        return emoji


@parser_base.register_parser_for(disnake.Sticker)
class GetStickerParser(parser_base.SourcedParser[disnake.Sticker]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAware
    ) -> disnake.Sticker:
        # <<docstring inherited from parser_api.Parser>>

        sticker = source.bot.get_sticker(int(argument))

        if sticker is None:
            msg = f"Could not find an emoji with id {argument!r}."
            raise LookupError(msg)

        return sticker


# GET AND FETCH


@parser_base.register_parser_for(disnake.Emoji)
class EmojiParser(parser_base.SourcedParser[disnake.Emoji]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

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

        return (
            source.bot.get_emoji(int(argument))
            or await source.guild.fetch_emoji(int(argument))
        )  # fmt: skip


@parser_base.register_parser_for(disnake.PartialEmoji)
class PartialEmojiParser(parser_base.Parser[disnake.PartialEmoji]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def dumps(self, __argument: disnake.PartialEmoji) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return str(__argument.id)

    def loads(self, argument: str) -> disnake.PartialEmoji:  # noqa: D102
        return disnake.PartialEmoji.from_dict({"id": int(argument)})


@parser_base.register_parser_for(disnake.Sticker)
class StickerParser(parser_base.SourcedParser[disnake.Sticker]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

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
        return (
            source.bot.get_sticker(int(argument))
            or await source.guild.fetch_sticker(int(argument))
        )  # fmt: skip
