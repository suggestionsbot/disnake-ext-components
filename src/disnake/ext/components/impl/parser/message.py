"""Parser implementations for disnake message types."""

from __future__ import annotations

import contextlib
import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import helpers

__all__: typing.Sequence[str] = (
    "PartialMessageParser",
    "GetMessageParser",
    "MessageParser",
)

AnyChannel = typing.Union[
    disnake.TextChannel,
    disnake.Thread,
    disnake.VoiceChannel,
    disnake.DMChannel,
    disnake.PartialMessageable,
]


@parser_base.register_parser_for(disnake.PartialMessage)
class PartialMessageParser(parser_base.SourcedParser[disnake.PartialMessage]):
    r"""Parser type with support for partial messages.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    channel:
        The channel in which to make the partial message.

        Defaults to ``None``. If left to be ``None``, :meth:`loads` will
        attempt to get a channel from the ``source``.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default message parser will also return compressed results.
    """
    channel: typing.Optional[AnyChannel]
    """The channel in which to make the partial message."""

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        channel: typing.Optional[AnyChannel] = None,
    ) -> None:
        self.int_parser = int_parser or builtins_parsers.IntParser.default()
        self.channel = channel

    def loads(self, argument: str, *, source: object) -> disnake.PartialMessage:
        """Load a partial message from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a partial message.
        source:
            The source to use for parsing.

            If :attr:`channel` is set, the source is ignored. Otherwise, this
            must be a channel, or be a type that has access to a
            :class:`channel <disnake.TextChannel>` attribute.

            .. note::
                This can be any channel type that supports
                `get_partial_message`.

        Raises
        ------
        :class:`RuntimeError`:
            :attr:`channel` was not set, and no channel could be obtained from
            the ``source``.

        """
        channel = self.channel
        if not channel:
            if isinstance(source, helpers.ChannelAware):
                channel = source.channel
            elif isinstance(source, helpers.PartialMessageAware):
                channel = source

        if not channel:
            msg = (
                "A channel must be provided either through self.channel or"
                " source.channel, got neither."
            )
            raise RuntimeError(msg)

        return channel.get_partial_message(self.int_parser.loads(argument))

    def dumps(self, argument: disnake.PartialMessage) -> str:
        """Dump a partial message into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Message)
class GetMessageParser(parser_base.SourcedParser[disnake.Message]):
    r"""Synchronous parser type with support for messages.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_fallback:
        If :meth:`loads` fails to get a result, the ``source`` is checked for
        a message. If the id of this message matches the provided ``argument``,
        it is returned. If ``allow_fallback`` is set to ``True``, the id
        validation is skipped, and the source message is always returned.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default message parser will also return compressed results.
    """
    allow_fallback: bool
    """If :meth:`loads` fails to get a result, the ``source`` is checked for
    a message. If the id of this message matches the provided ``argument``,
    it is returned. If ``allow_fallback`` is set to ``True``, the id
    validation is skipped, and the source message is always returned.

    .. warning::
        This can result in :meth:`loads` returning a message with an id that
        does not match the ``argument``.
    """

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_fallback: bool = False,
    ):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()
        self.allow_fallback = allow_fallback

    def loads(
        self,
        argument: str,
        *,
        source: typing.Union[helpers.BotAware, helpers.MessageAware],
    ) -> disnake.Message:
        """Load a message from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a message.
        source:
            The source to use for parsing.

            Must be a type that has access to a :class:`bot <commands.Bot>`
            or a :class:`message <disnake.Message>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A message with the id stored in the ``argument`` could not be found.

        """
        message_id = self.int_parser.loads(argument)

        if isinstance(source, helpers.BotAware):
            message = source.bot.get_message(message_id)
            if message:
                return message

        # If allow_fallback is True, return the source message regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, helpers.MessageAware)
            and (self.allow_fallback or source.message.id == message_id)
        ):  # fmt: skip
            return source.message

        msg = f"Could not find a message with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Message) -> str:
        """Dump a message into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Message)
class MessageParser(parser_base.SourcedParser[disnake.Message]):
    r"""Asynchronous parser type with support for messages.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_fallback:
        If :meth:`loads` fails to get a result, the ``source`` is checked for
        a message. If the id of this message matches the provided ``argument``,
        it is returned. If ``allow_fallback`` is set to ``True``, the id
        validation is skipped, and the source message is always returned.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default message parser will also return compressed results.
    """
    allow_fallback: bool
    """If :meth:`loads` fails to get a result, the ``source`` is checked for
    a message. If the id of this message matches the provided ``argument``,
    it is returned. If ``allow_fallback`` is set to ``True``, the id
    validation is skipped, and the source message is always returned.

    .. warning::
        This can result in :meth:`loads` returning a message with an id that
        does not match the ``argument``.
    """

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_fallback: bool = False,
    ):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()
        self.allow_fallback = allow_fallback

    async def loads(
        self,
        argument: str,
        *,
        source: typing.Union[
            helpers.BotAware,
            helpers.ChannelAware,
            helpers.MessageAware,
        ],
    ) -> disnake.Message:
        """Asynchronously load a message from a string.

        This uses the underlying :attr:`int_parser`.

        This method first tries to get the message from cache. If this fails,
        it will try to fetch the message instead.

        .. warning::
            This method can make API requests.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a message.
        source:
            The source to use for parsing.

            Must be a type that has access to a :class:`bot <commands.Bot>`,
            :class:`channel <disnake.Channel>` and/or
            :class:`message <disnake.Message>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A message with the id stored in the ``argument`` could not be found.

        """
        message_id = self.int_parser.loads(argument)
        if isinstance(source, helpers.BotAware):
            message = source.bot.get_message(message_id)
            if message:
                return message

        if isinstance(source, helpers.ChannelAware):
            with contextlib.suppress(disnake.HTTPException):
                message = await source.channel.fetch_message(message_id)
                if message:
                    return message

        # If allow_fallback is True, return the source message regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, helpers.MessageAware)
            and (self.allow_fallback or source.message.id == message_id)
        ):  # fmt: skip
            return source.message

        msg = f"Could not find a message with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Message) -> str:
        """Dump a message into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)
