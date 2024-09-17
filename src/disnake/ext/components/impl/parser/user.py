"""Parser implementations for disnake user types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import helpers, snowflake

__all__: typing.Sequence[str] = (
    "GetUserParser",
    "GetMemberParser",
    "UserParser",
    "MemberParser",
)


@parser_base.register_parser_for(disnake.User, disnake.abc.User)
class GetUserParser(parser_base.SourcedParser[disnake.User]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAware
    ) -> disnake.User:
        # <<docstring inherited from parser_api.Parser>>

        user = source.bot.get_user(int(argument))

        if user is None:
            msg = f"Could not find a user with id {argument!r}."
            raise LookupError(msg)

        return user


@parser_base.register_parser_for(disnake.Member)
class GetMemberParser(parser_base.SourcedParser[disnake.Member]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self,
        argument: str,
        *,
        source: typing.Union[
            helpers.GuildAware,
            helpers.MessageAware,
            helpers.ChannelAware,
        ],
    ) -> disnake.Member:
        # <<docstring inherited from parser_api.Parser>>

        guild = None
        if isinstance(source, helpers.GuildAware):
            guild = source.guild

        if guild is None and isinstance(source, helpers.MessageAware):
            guild = source.message.guild

        if guild is None:
            msg = (
                "Impossible to fetch a role from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)

        member = guild.get_member(int(argument))
        if member is not None:
            return member

        msg = f"Could not find a member with id {argument!r}."
        raise LookupError(msg)


@parser_base.register_parser_for(disnake.User)
class UserParser(parser_base.SourcedParser[disnake.User]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, argument: str, *, source: helpers.BotAware
    ) -> disnake.User:
        # <<docstring inherited from parser_api.Parser>>

        return (
            source.bot.get_user(int(argument))
            or await source.bot.fetch_user(int(argument))
        )  # fmt: skip


@parser_base.register_parser_for(disnake.Member)
class MemberParser(parser_base.SourcedParser[disnake.Member]):  # noqa: D101
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self,
        argument: str,
        *,
        source: typing.Union[
            helpers.GuildAware,
            helpers.MessageAware,
            helpers.ChannelAware,
        ],
    ) -> disnake.Member:
        # <<docstring inherited from parser_api.Parser>>

        guild = None
        if isinstance(source, helpers.GuildAware):
            guild = source.guild

        if guild is None and isinstance(source, helpers.MessageAware):
            guild = source.message.guild

        if (
            guild is None
            and isinstance(source, helpers.ChannelAware)
            and isinstance(source.channel, helpers.GuildAware)
        ):
            guild = source.channel.guild

        if guild is None:
            msg = (
                "Impossible to fetch a member from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)

        id_ = int(argument)
        return (
            guild.get_member(id_)
            or await guild.fetch_member(id_)
        )  # fmt: skip
