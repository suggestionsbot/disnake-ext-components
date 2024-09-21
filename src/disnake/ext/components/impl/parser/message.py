"""Parser implementations for disnake message types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import helpers

__all__: typing.Sequence[str] = (
    "GetMessageParser",
    "MessageParser",
    "PartialMessageParser",
)

AnyChannel = typing.Union[
    disnake.TextChannel,
    disnake.Thread,
    disnake.VoiceChannel,
    disnake.DMChannel,
    disnake.PartialMessageable,
]


@parser_base.register_parser_for(disnake.Message)
class GetMessageParser(parser_base.SourcedParser[disnake.Message]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser
    allow_fallback: bool

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_fallback: bool = False,
    ):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()
        self.allow_fallback = allow_fallback

    def loads(  # noqa: D102
        self,
        argument: str,
        *,
        source: typing.Union[helpers.BotAware, helpers.MessageAware],
    ) -> disnake.Message:
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

    def dumps(self, argument: disnake.Message) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Message)
class MessageParser(parser_base.SourcedParser[disnake.Message]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_fallback: bool = False,
    ):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()
        self.allow_fallback = allow_fallback

    async def loads(  # noqa: D102
        self,
        argument: str,
        *,
        source: typing.Union[
            helpers.BotAware,
            helpers.ChannelAware,
            helpers.MessageAware,
        ],
    ) -> disnake.Message:
        # <<docstring inherited from parser_api.Parser>>

        message_id = self.int_parser.loads(argument)
        if isinstance(source, helpers.BotAware):
            message = source.bot.get_message(message_id)
            if message:
                return message

        if isinstance(source, helpers.ChannelAware):
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

    def dumps(self, argument: disnake.Message) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.PartialMessage)
class PartialMessageParser(parser_base.SourcedParser[disnake.PartialMessage]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        channel: typing.Optional[AnyChannel] = None,
    ) -> None:
        self.int_parser = int_parser or builtins_parsers.IntParser.default()
        self.channel = channel

    def loads(  # noqa: D102
        self, argument: str, *, source: object
    ) -> disnake.PartialMessage:
        # <<docstring inherited from parser_api.Parser>>

        channel = self.channel
        if not channel and isinstance(source, helpers.ChannelAware):
            channel = source.channel

        if not channel:
            msg = (
                "A channel must be provided either through self.channel or"
                " source.channel, got neither."
            )
            raise RuntimeError(msg)

        return channel.get_partial_message(self.int_parser.loads(argument))

    def dumps(self, argument: disnake.PartialMessage) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)
