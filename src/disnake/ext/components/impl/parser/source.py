"""Module with helper protocols for parser source object annotations."""

import typing

import disnake
from disnake.ext import commands

__all__: typing.Sequence[str] = (
    "BotAware",
    "GuildAware",
    "MessageAware",
    "PartialMessageAware",
    "ChannelAware",
    "AuthorAware",
    "BotAndGuildAware",
    "get_guild_from_source",
)


_AnyBot = typing.Union[
    commands.Bot,
    commands.InteractionBot,
    commands.AutoShardedBot,
    commands.AutoShardedInteractionBot,
]
_AnyChannel = typing.Union[
    disnake.TextChannel,
    disnake.Thread,
    disnake.VoiceChannel,
    disnake.DMChannel,
    disnake.PartialMessageable,
]


@typing.runtime_checkable
class BotAware(typing.Protocol):
    """Protocol for a class that contains a reference to the bot."""

    @property
    def bot(self) -> _AnyBot:  # noqa: D102
        ...


@typing.runtime_checkable
class GuildAware(typing.Protocol):
    """Protocol for a class that contains a reference to a guild."""

    @property
    def guild(self) -> typing.Optional[disnake.Guild]:  # noqa: D102
        ...


@typing.runtime_checkable
class MessageAware(typing.Protocol):
    """Protocol for a class that contains a reference to a message."""

    @property
    def message(self) -> disnake.Message:  # noqa: D102
        ...


@typing.runtime_checkable
class PartialMessageAware(typing.Protocol):
    """Protocol for a class that can create partial messages."""

    def get_partial_message(  # noqa: D102
        self, message_id: int, /
    ) -> disnake.PartialMessage:
        ...


@typing.runtime_checkable
class ChannelAware(typing.Protocol):
    """Protocol for a class that contains a reference to a channel."""

    @property
    def channel(self) -> _AnyChannel:  # noqa: D102
        ...


@typing.runtime_checkable
class AuthorAware(typing.Protocol):
    """Protocol for a class that contains a reference to an author."""

    @property
    def author(self) -> typing.Union[disnake.User, disnake.Member]:  # noqa: D102
        ...


class BotAndGuildAware(BotAware, GuildAware, typing.Protocol):
    """Protocol for a class that contains a refernce to the bot and a guild."""


def get_guild_from_source(source: object) -> disnake.Guild:
    """Try to get a guild from various source types."""
    if isinstance(source, GuildAware) and source.guild:
        return source.guild

    if isinstance(source, MessageAware):
        return get_guild_from_source(source.message)

    if isinstance(source, ChannelAware):
        return get_guild_from_source(source.channel)

    if isinstance(source, AuthorAware) and isinstance(source.author, disnake.Member):
        return get_guild_from_source(source.author)

    msg = "Cannot get a role from an object that doesn't reference a guild."
    raise TypeError(msg)
