"""Parser implementations for disnake channel types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import helpers

if typing.TYPE_CHECKING:
    from disnake.ext import commands

    _AnyBot = typing.Union[
        commands.Bot,
        commands.InteractionBot,
        commands.AutoShardedBot,
        commands.AutoShardedInteractionBot,
    ]


__all__: typing.Sequence[str] = (
    "DMChannelParser",
    "ForumChannelParser",
    "GroupChannelParser",
    "GuildChannelParser",
    "PrivateChannelParser",
    "NewsChannelParser",
    "StageChannelParser",
    "TextChannelParser",
    "ThreadParser",
    "VoiceChannelParser",
    "CategoryParser",
    "GetDMChannelParser",
    "GetForumChannelParser",
    "GetGroupChannelParser",
    "GetGuildChannelParser",
    "GetPrivateChannelParser",
    "GetNewsChannelParser",
    "GetStageChannelParser",
    "GetTextChannelParser",
    "GetThreadParser",
    "GetVoiceChannelParser",
    "GetCategoryParser",
    "PartialMessageableParser",
)


_AnyChannel = typing.Union[
    disnake.abc.GuildChannel, disnake.abc.PrivateChannel, disnake.Thread
]
_ChannelT = typing.TypeVar("_ChannelT", bound=_AnyChannel)


def _get_source(
    source: typing.Union[helpers.GuildAware, helpers.BotAware, helpers.MessageAware],
) -> typing.Union[disnake.Guild, _AnyBot]:
    actual_source = None
    if isinstance(source, helpers.BotAware):
        actual_source = source.bot

    if actual_source is None and isinstance(source, helpers.MessageAware):
        actual_source = source.message.guild

    if actual_source is None and isinstance(source, helpers.GuildAware):
        actual_source = source.guild

    if actual_source is not None:
        return actual_source

    # TODO: In the future handle just returning message.channel if it
    #       is a DM channel and the id matches the argument.
    msg = "Parsing DM channels from a message is currently not supported."
    raise NotImplementedError(msg)


# GET_ONLY


class GetChannelParserBase(parser_base.SourcedParser[_ChannelT]):
    # <<docstring inherited from parser_api.Parser>>

    parser_type: typing.Type[_ChannelT]
    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(
        self,
        argument: str,
        *,
        source: typing.Union[
            helpers.GuildAware, helpers.BotAware, helpers.MessageAware
        ],
    ) -> _ChannelT:
        # <<docstring inherited from parser_api.Parser>>

        channel_id = self.int_parser.loads(argument)
        channel = _get_source(source).get_channel(channel_id)

        if channel is None:
            msg = f"Could not find a channel with id {argument!r}."
            raise LookupError(msg)

        if not isinstance(channel, self.parser_type):
            msg = (
                f"Found a channel of type {type(channel).__name__!r} for id"
                f" {argument!r}, expected type {self.parser_type.__name__!r}."
            )
            raise TypeError(msg)
        return channel

    def dumps(self, argument: _ChannelT) -> str:
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


# GET AND FETCH


class ChannelParserBase(parser_base.SourcedParser[_ChannelT]):
    # <<docstring inherited from parser_api.Parser>>

    parser_type: typing.Type[_ChannelT]
    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    async def loads(self, argument: str, *, source: disnake.Interaction) -> _ChannelT:
        # <<docstring inherited from parser_api.Parser>>

        channel_id = self.int_parser.loads(argument)
        channel = (
            source.bot.get_channel(channel_id)
            or await source.bot.fetch_channel(channel_id)
        )  # fmt: skip

        if not isinstance(channel, self.parser_type):
            msg = (
                f"Found a channel of type {type(channel).__name__!r} for id"
                f" {argument!r}, expected type {self.parser_type.__name__!r}."
            )
            raise TypeError(msg)
        return channel

    def dumps(self, argument: _ChannelT) -> str:
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


# ABSTRACT


@parser_base.register_parser_for(disnake.abc.GuildChannel)
class GetGuildChannelParser(GetChannelParserBase[disnake.abc.GuildChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.abc.GuildChannel


@parser_base.register_parser_for(disnake.abc.PrivateChannel)
class GetPrivateChannelParser(GetChannelParserBase[disnake.abc.PrivateChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.abc.PrivateChannel  # pyright: ignore[reportAssignmentType]


# PRIVATE


@parser_base.register_parser_for(disnake.DMChannel)
class GetDMChannelParser(GetChannelParserBase[disnake.DMChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.DMChannel


@parser_base.register_parser_for(disnake.GroupChannel)
class GetGroupChannelParser(GetChannelParserBase[disnake.GroupChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.GroupChannel


# GUILD


@parser_base.register_parser_for(disnake.ForumChannel)
class GetForumChannelParser(GetChannelParserBase[disnake.ForumChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.ForumChannel


@parser_base.register_parser_for(disnake.NewsChannel)
class GetNewsChannelParser(GetChannelParserBase[disnake.NewsChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.NewsChannel


@parser_base.register_parser_for(disnake.VoiceChannel)
class GetVoiceChannelParser(GetChannelParserBase[disnake.VoiceChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.VoiceChannel


@parser_base.register_parser_for(disnake.StageChannel)
class GetStageChannelParser(GetChannelParserBase[disnake.StageChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.StageChannel


@parser_base.register_parser_for(disnake.TextChannel)
class GetTextChannelParser(GetChannelParserBase[disnake.TextChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.TextChannel


@parser_base.register_parser_for(disnake.Thread)
class GetThreadParser(GetChannelParserBase[disnake.Thread]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.Thread


@parser_base.register_parser_for(disnake.CategoryChannel)
class GetCategoryParser(GetChannelParserBase[disnake.CategoryChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.CategoryChannel


# ASYNC ABSTRACT


@parser_base.register_parser_for(disnake.abc.GuildChannel)
class GuildChannelParser(ChannelParserBase[disnake.abc.GuildChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.abc.GuildChannel


@parser_base.register_parser_for(disnake.abc.PrivateChannel)
class PrivateChannelParser(ChannelParserBase[disnake.abc.PrivateChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.abc.PrivateChannel  # pyright: ignore[reportAssignmentType]


# ASYNC PRIVATE


@parser_base.register_parser_for(disnake.DMChannel)
class DMChannelParser(ChannelParserBase[disnake.DMChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.DMChannel


@parser_base.register_parser_for(disnake.GroupChannel)
class GroupChannelParser(ChannelParserBase[disnake.GroupChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.GroupChannel


# ASYNC GUILD


@parser_base.register_parser_for(disnake.ForumChannel)
class ForumChannelParser(ChannelParserBase[disnake.ForumChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.ForumChannel


@parser_base.register_parser_for(disnake.NewsChannel)
class NewsChannelParser(ChannelParserBase[disnake.NewsChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.NewsChannel


@parser_base.register_parser_for(disnake.VoiceChannel)
class VoiceChannelParser(ChannelParserBase[disnake.VoiceChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.VoiceChannel


@parser_base.register_parser_for(disnake.StageChannel)
class StageChannelParser(ChannelParserBase[disnake.StageChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.StageChannel


@parser_base.register_parser_for(disnake.TextChannel)
class TextChannelParser(ChannelParserBase[disnake.TextChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.TextChannel


@parser_base.register_parser_for(disnake.Thread)
class ThreadParser(ChannelParserBase[disnake.Thread]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.Thread


@parser_base.register_parser_for(disnake.CategoryChannel)
class CategoryParser(ChannelParserBase[disnake.CategoryChannel]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>
    parser_type = disnake.CategoryChannel


@parser_base.register_parser_for(disnake.PartialMessageable)
class PartialMessageableParser(parser_base.SourcedParser[disnake.PartialMessageable]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    channel_type: typing.Optional[disnake.ChannelType]
    int_parser: builtins_parsers.IntParser

    def __init__(
        self,
        channel_type: typing.Optional[disnake.ChannelType] = None,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
    ) -> None:
        self.channel_type = channel_type
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAware
    ) -> disnake.PartialMessageable:
        # <<docstring inherited from parser_api.Parser>>

        return source.bot.get_partial_messageable(int(argument), type=self.channel_type)

    def dumps(self, argument: disnake.PartialMessageable) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)
