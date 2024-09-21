"""Parser implementations for disnake user types."""

from __future__ import annotations

import contextlib
import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import helpers

__all__: typing.Sequence[str] = (
    "GetUserParser",
    "GetMemberParser",
    "UserParser",
    "MemberParser",
)


@parser_base.register_parser_for(disnake.User, disnake.abc.User)
class GetUserParser(parser_base.SourcedParser[disnake.User]):  # noqa: D101
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
        source: typing.Union[helpers.BotAware, helpers.AuthorAware],
    ) -> disnake.User:
        # <<docstring inherited from parser_api.Parser>>

        user_id = self.int_parser.loads(argument)
        if isinstance(source, helpers.BotAware):
            user = source.bot.get_user(user_id)
            if user:
                return user

        # First, validate that the source author is a member.
        # If allow_fallback is True, return the source member regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, helpers.AuthorAware)
            and isinstance(source.author, disnake.User)
            and (self.allow_fallback or source.author.id == user_id)
        ):
            return source.author

        msg = f"Could not find a user with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.User) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Member)
class GetMemberParser(parser_base.SourcedParser[disnake.Member]):  # noqa: D101
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
        source: typing.Union[
            helpers.GuildAware,
            helpers.MessageAware,
            helpers.ChannelAware,
            helpers.AuthorAware,
        ],
    ) -> disnake.Member:
        # <<docstring inherited from parser_api.Parser>>

        guild = helpers.get_guild_from_source(source)
        member_id = self.int_parser.loads(argument)

        member = guild.get_member(member_id)
        if member:
            return member

        # First, validate that the source author is a member.
        # If allow_fallback is True, return the source member regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, helpers.AuthorAware)
            and isinstance(source.author, disnake.Member)
            and (self.allow_fallback or source.author.id == member_id)
        ):
            return source.author

        msg = f"Could not find a member with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Member) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.User)
class UserParser(parser_base.SourcedParser[disnake.User]):  # noqa: D101
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
        source: typing.Union[helpers.BotAware, helpers.AuthorAware],
    ) -> disnake.User:
        # <<docstring inherited from parser_api.Parser>>

        user_id = self.int_parser.loads(argument)
        if isinstance(source, helpers.BotAware):
            user = source.bot.get_user(user_id)
            if user:
                return user

            with contextlib.suppress(disnake.HTTPException):
                return await source.bot.fetch_user(user_id)

        # First, validate that the source author is a member.
        # If allow_fallback is True, return the source member regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, helpers.AuthorAware)
            and isinstance(source.author, disnake.User)
            and (self.allow_fallback or source.author.id == user_id)
        ):
            return source.author

        msg = f"Could not find a user with id {argument!r}."
        raise LookupError(msg)


@parser_base.register_parser_for(disnake.Member)
class MemberParser(parser_base.SourcedParser[disnake.Member]):  # noqa: D101
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
        source: typing.Union[
            helpers.GuildAware,
            helpers.MessageAware,
            helpers.ChannelAware,
            helpers.AuthorAware,
        ],
    ) -> disnake.Member:
        # <<docstring inherited from parser_api.Parser>>

        guild = helpers.get_guild_from_source(source)

        member_id = self.int_parser.loads(argument)
        member = guild.get_member(member_id)
        if member:
            return member

        with contextlib.suppress(disnake.HTTPException):
            return await guild.fetch_member(member_id)

        # First, validate that the source author is a member.
        # If allow_fallback is True, return the source member regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, helpers.AuthorAware)
            and isinstance(source.author, disnake.Member)
            and (self.allow_fallback or source.author.id == member_id)
        ):
            return source.author

        msg = f"Could not find a member with id {argument!r}."
        raise LookupError(msg)
