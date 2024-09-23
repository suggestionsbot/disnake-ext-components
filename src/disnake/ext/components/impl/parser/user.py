"""Parser implementations for disnake user types."""

from __future__ import annotations

import contextlib
import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import source as parser_source

__all__: typing.Sequence[str] = (
    "GetUserParser",
    "GetMemberParser",
    "UserParser",
    "MemberParser",
)


@parser_base.register_parser_for(disnake.User, disnake.abc.User)
class GetUserParser(parser_base.SourcedParser[disnake.User]):
    r"""Synchronous parser type with support for users.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_fallback:
        If :meth:`loads` fails to get a result, the ``source`` is checked for
        a user. If the id of this user matches the provided ``argument``, it
        is returned. If ``allow_fallback`` is set to ``True``, the id
        validation is skipped, and the source user is always returned.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default user parser will also return compressed results.
    """
    allow_fallback: bool
    """If :meth:`loads` fails to get a result, the ``source`` is checked for
    a user. If the id of this user matches the provided ``argument``, it is
    returned. If ``allow_fallback`` is set to ``True``, the id validation is
    skipped, and the source user is always returned.

    .. warning::
        This can result in :meth:`loads` returning a user with an id that
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
        source: typing.Union[parser_source.BotAware, parser_source.AuthorAware],
    ) -> disnake.User:
        """Load a user from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a user.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`bot <disnake.ext.commands.Bot>` or a
            :class:`author <disnake.User>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A user with the id stored in the ``argument`` could not be found.

        """
        user_id = self.int_parser.loads(argument)
        if isinstance(source, parser_source.BotAware):
            user = source.bot.get_user(user_id)
            if user:
                return user

        # First, validate that the source author is a user.
        # If allow_fallback is True, return the source user regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, parser_source.AuthorAware)
            and isinstance(source.author, disnake.User)
            and (self.allow_fallback or source.author.id == user_id)
        ):
            return source.author

        msg = f"Could not find a user with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.User) -> str:
        """Dump a user into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Member)
class GetMemberParser(parser_base.SourcedParser[disnake.Member]):
    r"""Synchronous parser type with support for members.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_fallback:
        If :meth:`loads` fails to get a result, the ``source`` is checked for
        a member. If the id of this member matches the provided ``argument``,
        it is returned. If ``allow_fallback`` is set to ``True``, the id
        validation is skipped, and the source member is always returned.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default member parser will also return compressed results.
    """
    allow_fallback: bool
    """If :meth:`loads` fails to get a result, the ``source`` is checked for
    a member. If the id of this member matches the provided ``argument``, it is
    returned. If ``allow_fallback`` is set to ``True``, the id validation is
    skipped, and the source member is always returned.

    .. warning::
        This can result in :meth:`loads` returning a member with an id that
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
        source: typing.Union[
            parser_source.GuildAware,
            parser_source.MessageAware,
            parser_source.ChannelAware,
            parser_source.AuthorAware,
        ],
    ) -> disnake.Member:
        """Load a member from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a member.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`guild <disnake.Guild>`, :class:`message <disnake.Message>`,
            :class:`channel <disnake.Channel>`, or a
            :class:`author <disnake.Member>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A member with the id stored in the ``argument`` could not be found.

        """
        guild = parser_source.get_guild_from_source(source)
        member_id = self.int_parser.loads(argument)

        member = guild.get_member(member_id)
        if member:
            return member

        # First, validate that the source author is a member.
        # If allow_fallback is True, return the source member regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, parser_source.AuthorAware)
            and isinstance(source.author, disnake.Member)
            and (self.allow_fallback or source.author.id == member_id)
        ):
            return source.author

        msg = f"Could not find a member with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Member) -> str:
        """Dump a member into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.User)
class UserParser(parser_base.SourcedParser[disnake.User]):
    r"""Asynchronous parser type with support for users.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_fallback:
        If :meth:`loads` fails to get a result, the ``source`` is checked for
        a user. If the id of this user matches the provided ``argument``, it
        is returned. If ``allow_fallback`` is set to ``True``, the id
        validation is skipped, and the source user is always returned.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default user parser will also return compressed results.
    """
    allow_fallback: bool
    """If :meth:`loads` fails to get a result, the ``source`` is checked for
    a user. If the id of this user matches the provided ``argument``, it is
    returned. If ``allow_fallback`` is set to ``True``, the id validation is
    skipped, and the source user is always returned.

    .. warning::
        This can result in :meth:`loads` returning a user with an id that
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
        source: typing.Union[parser_source.BotAware, parser_source.AuthorAware],
    ) -> disnake.User:
        """Asynchronously load a user from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a user.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`bot <disnake.ext.commands.Bot>` or a
            :class:`author <disnake.User>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A user with the id stored in the ``argument`` could not be found.

        """
        user_id = self.int_parser.loads(argument)
        if isinstance(source, parser_source.BotAware):
            user = source.bot.get_user(user_id)
            if user:
                return user

            with contextlib.suppress(disnake.HTTPException):
                return await source.bot.fetch_user(user_id)

        # First, validate that the source author is a user.
        # If allow_fallback is True, return the source user regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, parser_source.AuthorAware)
            and isinstance(source.author, disnake.User)
            and (self.allow_fallback or source.author.id == user_id)
        ):
            return source.author

        msg = f"Could not find a user with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.User) -> str:
        """Dump a user into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Member)
class MemberParser(parser_base.SourcedParser[disnake.Member]):
    r"""Asynchronous parser type with support for members.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_fallback:
        If :meth:`loads` fails to get a result, the ``source`` is checked for
        a member. If the id of this member matches the provided ``argument``, it
        is returned. If ``allow_fallback`` is set to ``True``, the id
        validation is skipped, and the source member is always returned.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default member parser will also return compressed results.
    """
    allow_fallback: bool
    """If :meth:`loads` fails to get a result, the ``source`` is checked for
    a member. If the id of this member matches the provided ``argument``, it is
    returned. If ``allow_fallback`` is set to ``True``, the id validation is
    skipped, and the source member is always returned.

    .. warning::
        This can result in :meth:`loads` returning a member with an id that
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
            parser_source.GuildAware,
            parser_source.MessageAware,
            parser_source.ChannelAware,
            parser_source.AuthorAware,
        ],
    ) -> disnake.Member:
        """Asynchronously load a member from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a member.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`guild <disnake.Guild>`, :class:`message <disnake.Message>`,
            :class:`channel <disnake.Channel>`, or a
            :class:`author <disnake.Member>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A member with the id stored in the ``argument`` could not be found.

        """
        guild = parser_source.get_guild_from_source(source)

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
            isinstance(source, parser_source.AuthorAware)
            and isinstance(source.author, disnake.Member)
            and (self.allow_fallback or source.author.id == member_id)
        ):
            return source.author

        msg = f"Could not find a member with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Member) -> str:
        """Dump a user into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)
