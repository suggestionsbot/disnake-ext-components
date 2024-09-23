"""Parser implementations for disnake emoji types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import source as parser_source

__all__: typing.Sequence[str] = (
    "PartialEmojiParser",
    "GetEmojiParser",
    "EmojiParser",
    "GetStickerParser",
    "StickerParser",
)


# GET_ONLY


# TODO: Probably need to implement animated, maybe also name
# TODO: Maybe implement some way of *not* requiring ids for partial emoji
@parser_base.register_parser_for(disnake.PartialEmoji)
class PartialEmojiParser(parser_base.Parser[disnake.PartialEmoji]):
    r"""Parser type with support for partial emoji.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default partial emoji parser will also return compressed results.
    """

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(self, argument: str) -> disnake.PartialEmoji:
        """Load a partial emoji from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a partial emoji.
        source:
            The source to use for parsing.

            Must be a type that has access to a :class:`bot <commands.Bot>`
            attribute.

        """
        return disnake.PartialEmoji.from_dict({"id": self.int_parser.loads(argument)})

    def dumps(self, argument: disnake.PartialEmoji) -> str:
        """Dump a partial emoji into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        if not argument.id:
            msg = "PartialEmojiParser requires PartialEmoji.id to be set."
            raise ValueError(msg)

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Emoji)
class GetEmojiParser(parser_base.SourcedParser[disnake.Emoji]):
    """Synchronous parser type with support for emoji.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default emoji parser will also return compressed results.
    """

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(self, argument: str, *, source: parser_source.BotAware) -> disnake.Emoji:
        """Load an emoji from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into an emoji.
        source:
            The source to use for parsing.

            Must be a type that has access to a :class:`bot <commands.Bot>`
            attribute.

        Raises
        ------
        :class:`LookupError`:
            An emoji with the id stored in the ``argument`` could not be found.

        """
        emoji = source.bot.get_emoji(self.int_parser.loads(argument))

        if emoji is None:
            msg = f"Could not find an emoji with id {argument!r}."
            raise LookupError(msg)

        return emoji

    def dumps(self, argument: disnake.Emoji) -> str:
        """Dump an emoji into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Sticker)
class GetStickerParser(parser_base.SourcedParser[disnake.Sticker]):
    """Synchronous parser type with support for stickers.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default sticker parser will also return compressed results.
    """

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(
        self,
        argument: str,
        *,
        source: parser_source.BotAware,
    ) -> disnake.Sticker:
        """Load a sticker from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a sticker.
        source:
            The source to use for parsing.

            Must be a type that has access to a :class:`bot <commands.Bot>`
            attribute.

        Raises
        ------
        :class:`LookupError`:
            A sticker with the id stored in the ``argument`` could not be found.

        """
        sticker = source.bot.get_sticker(self.int_parser.loads(argument))

        if sticker is None:
            msg = f"Could not find an emoji with id {argument!r}."
            raise LookupError(msg)

        return sticker

    def dumps(self, argument: disnake.Sticker) -> str:
        """Dump a sticker into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


# GET AND FETCH


@parser_base.register_parser_for(disnake.Emoji)
class EmojiParser(parser_base.SourcedParser[disnake.Emoji]):
    """Asynchronous parser type with support for emoji.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default emoji parser will also return compressed results.
    """

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    async def loads(
        self, argument: str, *, source: parser_source.BotAndGuildAware
    ) -> disnake.Emoji:
        """Asynchronously load an emoji from a string.

        This uses the underlying :attr:`int_parser`.

        This method first tries to get the emoji from cache. If this fails,
        it will try to fetch the emoji instead.

        .. warning::
            This method can make API requests.

        Parameters
        ----------
        argument:
            The value that is to be loaded into an emoji.
        source:
            The source to use for parsing.

            Must be a type that has access to both :class:`bot <commands.Bot>`
            and :class:`guild <disnake.Guild>` attributes.

        Raises
        ------
        :class:`TypeError`:
            The provided ``source`` does not define a guild and global cache
            lookup failed.
        ...:
            Any exception raised by
            :meth:`Guild.fetch_emoji <disnake.Guild.fetch_emoji>`.

        """
        emoji_id = self.int_parser.loads(argument)
        emoji = source.bot.get_emoji(emoji_id)
        if emoji:
            return emoji

        if source.guild is None:
            msg = (
                "Impossible to fetch an emoji from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)

        return await source.guild.fetch_emoji(emoji_id)

    def dumps(self, argument: disnake.Emoji) -> str:
        """Dump an emoji into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Sticker)
class StickerParser(parser_base.SourcedParser[disnake.Sticker]):
    """Asynchronous parser type with support for stickers.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default emoji parser will also return compressed results.
    """

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    async def loads(
        self, argument: str, *, source: parser_source.BotAndGuildAware
    ) -> disnake.Sticker:
        """Asynchronously load a sticker from a string.

        This uses the underlying :attr:`int_parser`.

        This method first tries to get the sticker from cache. If this fails,
        it will try to fetch the sticker instead.

        .. warning::
            This method can make API requests.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a sticker.
        source:
            The source to use for parsing.

            Must be a type that has access to both :class:`bot <commands.Bot>`
            and :class:`guild <disnake.Guild>` attributes.

        Raises
        ------
        :class:`TypeError`:
            The provided ``source`` does not define a guild and global cache
            lookup failed.
        ...:
            Any exception raised by
            :meth:`Guild.fetch_sticker <disnake.Guild.fetch_sticker>`.

        """
        sticker_id = self.int_parser.loads(argument)
        sticker = source.bot.get_sticker(sticker_id)
        if sticker:
            return sticker

        if source.guild is None:
            msg = (
                "Impossible to fetch a sticker from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)

        return await source.guild.fetch_sticker(sticker_id)

    def dumps(self, argument: disnake.Sticker) -> str:
        """Dump a sticker into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)
