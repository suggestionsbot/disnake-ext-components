"""Parser implementations for disnake.Guild type."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import helpers

__all__: typing.Sequence[str] = (
    "GuildParser",
    "GetGuildParser",
    "InviteParser",
    "RoleParser",
    "GetRoleParser",
)


def _get_guild_from_source(
    source: object,
) -> disnake.Guild:
    if isinstance(source, helpers.GuildAware) and source.guild:
        return source.guild

    if isinstance(source, helpers.MessageAware):
        return _get_guild_from_source(source.message)

    if isinstance(source, helpers.ChannelAware):
        return _get_guild_from_source(source.channel)

    msg = "Cannot get a role from an object that doesn't reference a guild."
    raise TypeError(msg)


@parser_base.register_parser_for(disnake.Guild)
class GetGuildParser(parser_base.SourcedParser[disnake.Guild]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser

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
        source: typing.Union[helpers.BotAware, helpers.GuildAware],
    ) -> disnake.Guild:
        # <<docstring inherited from parser_api.Parser>>

        guild_id = self.int_parser.loads(argument)

        if isinstance(source, helpers.BotAware):
            guild = source.bot.get_guild(guild_id)
            if guild:
                return guild

        # If allow_fallback is True, return the guild regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, helpers.GuildAware)
            and source.guild
            and (self.allow_fallback or source.guild.id == guild_id)
        ):
            return source.guild

        msg = f"Could not find a guild with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Guild) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Guild)
class GuildParser(parser_base.SourcedParser[disnake.Guild]):  # noqa: D101
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

    async def loads(  # noqa: D102
        self,
        argument: str,
        *,
        source: typing.Union[helpers.BotAware, helpers.GuildAware],
    ) -> disnake.Guild:
        # <<docstring inherited from parser_api.Parser>>

        guild_id = self.int_parser.loads(argument)
        if isinstance(source, helpers.BotAware):
            guild = source.bot.get_guild(guild_id)
            if guild:
                return guild

            try:
                return await source.bot.fetch_guild(guild_id)
            except disnake.HTTPException:
                pass

        # If allow_fallback is True, return the source guild regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, helpers.GuildAware)
            and source.guild
            and (self.allow_fallback or source.guild.id == guild_id)
        ):
            return source.guild

        msg = f"Could not find a guild with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Guild) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Invite)
class InviteParser(parser_base.SourcedParser[disnake.Invite]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(
        self,
        *,
        with_counts: bool = True,
        with_expiration: bool = True,
        guild_scheduled_event_id: typing.Optional[int] = None,
    ) -> None:
        self.with_counts = with_counts
        self.with_expiration = with_expiration
        self.guild_scheduled_event_id = guild_scheduled_event_id

    async def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAware
    ) -> disnake.Invite:
        # <<docstring inherited from parser_api.Parser>>

        return await source.bot.fetch_invite(
            argument,
            with_counts=self.with_counts,
            with_expiration=self.with_expiration,
            guild_scheduled_event_id=self.guild_scheduled_event_id,
        )

    def dumps(self, argument: disnake.Invite) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return argument.id


@parser_base.register_parser_for(disnake.Role)
class GetRoleParser(parser_base.SourcedParser[disnake.Role]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    def loads(  # noqa: D102
        self,
        argument: str,
        *,
        source: typing.Union[
            helpers.GuildAware,
            helpers.MessageAware,
            helpers.ChannelAware,
        ],
    ) -> disnake.Role:
        # <<docstring inherited from parser_api.Parser>>

        guild = _get_guild_from_source(source)
        role_id = self.int_parser.loads(argument)

        role = guild.get_role(role_id)
        if role:
            return role

        msg = f"Could not find a role with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Role) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Role)
class RoleParser(parser_base.SourcedParser[disnake.Role]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    int_parser: builtins_parsers.IntParser

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default()

    async def loads(  # noqa: D102
        self,
        argument: str,
        *,
        source: typing.Union[
            helpers.GuildAware,
            helpers.MessageAware,
            helpers.ChannelAware,
        ],
    ) -> disnake.Role:
        # <<docstring inherited from parser_api.Parser>>

        guild = _get_guild_from_source(source)
        role_id = self.int_parser.loads(argument)

        role = guild.get_role(role_id)
        if role is not None:
            return role

        for role in await guild.fetch_roles():
            if role.id == role_id:
                return role

        # A role id coming from a custom_id could be of a deleted role object
        # so we're handling that possibility.
        msg = f"Could not find a role with id {argument!r}."
        raise LookupError(msg)
