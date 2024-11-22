"""Parser implementations for disnake.Guild type."""

from __future__ import annotations

import contextlib
import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.impl.parser import source as parser_source

__all__: typing.Sequence[str] = (
    "GuildParser",
    "GetGuildParser",
    "InviteParser",
    "RoleParser",
    "GetRoleParser",
)


@parser_base.register_parser_for(disnake.Guild)
class GetGuildParser(parser_base.SourcedParser[disnake.Guild]):
    r"""Synchronous parser type with support for guilds.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_fallback:
        If :meth:`loads` fails to get a result, the ``source`` is checked for
        a guild. If the id of this guild matches the provided ``argument``, it
        is returned. If ``allow_fallback`` is set to ``True``, the id
        validation is skipped, and the source channel is always returned.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default guild parser will also return compressed results.
    """
    allow_fallback: bool
    """If :meth:`loads` fails to get a result, the ``source`` is checked for
    a guild. If the id of this guild matches the provided ``argument``, it
    is returned. If ``allow_fallback`` is set to ``True``, the id
    validation is skipped, and the source channel is always returned.

    .. warning::
        This can result in :meth:`loads` returning a guild with an id that
        does not match the ``argument``.
    """

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_fallback: bool = False,
    ):
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)
        self.allow_fallback = allow_fallback

    def loads(
        self,
        argument: str,
        *,
        source: typing.Union[parser_source.BotAware, parser_source.GuildAware],
    ) -> disnake.Guild:
        """Load a guild from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a guild.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`bot <disnake.ext.commands.Bot>` or a
            :class:`guild <disnake.Guild>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A guild with the id stored in the ``argument`` could not be found.

        """
        guild_id = self.int_parser.loads(argument)

        if isinstance(source, parser_source.BotAware):
            guild = source.bot.get_guild(guild_id)
            if guild:
                return guild

        # If allow_fallback is True, return the guild regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, parser_source.GuildAware)
            and source.guild
            and (self.allow_fallback or source.guild.id == guild_id)
        ):
            return source.guild

        msg = f"Could not find a guild with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Guild) -> str:
        """Dump a guild into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Guild)
class GuildParser(parser_base.SourcedParser[disnake.Guild]):
    r"""Asynchronous parser type with support for guilds.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_fallback:
        If :meth:`loads` fails to get a result, the ``source`` is checked for
        a guild. If the id of this guild matches the provided ``argument``, it
        is returned. If ``allow_fallback`` is set to ``True``, the id
        validation is skipped, and the source channel is always returned.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default guild parser will also return compressed results.
    """
    allow_fallback: bool
    """If :meth:`loads` fails to get a result, the ``source`` is checked for
    a guild. If the id of this guild matches the provided ``argument``, it
    is returned. If ``allow_fallback`` is set to ``True``, the id
    validation is skipped, and the source channel is always returned.

    .. warning::
        This can result in :meth:`loads` returning a guild with an id that
        does not match the ``argument``.
    """

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_fallback: bool = False,
    ):
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)
        self.allow_fallback = allow_fallback

    async def loads(
        self,
        argument: str,
        *,
        source: typing.Union[parser_source.BotAware, parser_source.GuildAware],
    ) -> disnake.Guild:
        """Asynchronously load a guild from a string.

        This uses the underlying :attr:`int_parser`.

        This method first tries to get the guild from cache. If this fails,
        it will try to fetch the guild instead.

        .. warning::
            This method can make API requests.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a guild.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`bot <disnake.ext.commands.Bot>` or a
            :class:`guild <disnake.Guild>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A guild with the id stored in the ``argument`` could not be found.

        """
        guild_id = self.int_parser.loads(argument)
        if isinstance(source, parser_source.BotAware):
            guild = source.bot.get_guild(guild_id)
            if guild:
                return guild

            with contextlib.suppress(disnake.HTTPException):
                return await source.bot.fetch_guild(guild_id)

        # If allow_fallback is True, return the source guild regardless of
        # whether the id is correct. Otherwise, validate the id.
        if (
            isinstance(source, parser_source.GuildAware)
            and source.guild
            and (self.allow_fallback or source.guild.id == guild_id)
        ):
            return source.guild

        msg = f"Could not find a guild with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Guild) -> str:
        """Dump a guild into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Invite)
class InviteParser(parser_base.SourcedParser[disnake.Invite]):
    """Asynchronous parser type with support for guilds.

    .. warning::
        This parser can make API requests.


    Parameters
    ----------
    with_counts:
        Whether to include count information in the invite.
    with_expiration:
        Whether to include the expiration date of the invite.
    guild_scheduled_event_id: :class:`int`
        The ID of the scheduled event to include in the invite.

        If not provided, defaults to the ``event`` parameter in the URL if
        it exists, or the ID of the scheduled event contained in the
        provided invite object.

    """

    with_counts: bool
    """Whether to include the number of times an invite was used."""
    with_expiration: bool
    """Whether to include when the invite expires."""
    guild_scheduled_event_id: typing.Optional[int]
    """The ID of the scheduled event to include in the invite."""

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

    async def loads(
        self,
        argument: str,
        *,
        source: parser_source.BotAware,
    ) -> disnake.Invite:
        """Asynchronously load a guild invite from a string.

        This uses the underlying :attr:`int_parser`.

        This method first tries to get the invite from cache. If this fails,
        it will try to fetch the invite instead.

        .. warning::
            This method can make API requests.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a guild invite.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`bot <disnake.ext.commands.Bot>` attribute.

        """
        return await source.bot.fetch_invite(
            argument,
            with_counts=self.with_counts,
            with_expiration=self.with_expiration,
            guild_scheduled_event_id=self.guild_scheduled_event_id,
        )

    def dumps(self, argument: disnake.Invite) -> str:
        """Dump a guild invite into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return argument.id


@parser_base.register_parser_for(disnake.Role)
class GetRoleParser(parser_base.SourcedParser[disnake.Role]):
    r"""Synchronous parser type with support for roles.

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
    default role parser will also return compressed results.
    """

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)

    def loads(
        self,
        argument: str,
        *,
        source: typing.Union[
            parser_source.GuildAware,
            parser_source.MessageAware,
            parser_source.ChannelAware,
        ],
    ) -> disnake.Role:
        """Load a role from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a role.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`guild <disnake.Guild>`, :class:`message <disnake.Message>`,
            or a :class:`channel <disnake.TextChannel>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A role with the id stored in the ``argument`` could not be found.

        """
        guild = parser_source.get_guild_from_source(source)
        role_id = self.int_parser.loads(argument)

        role = guild.get_role(role_id)
        if role:
            return role

        msg = f"Could not find a role with id {argument!r}."
        raise LookupError(msg)

    def dumps(self, argument: disnake.Role) -> str:
        """Dump a role into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Role)
class RoleParser(parser_base.SourcedParser[disnake.Role]):
    r"""Asynchronous parser type with support for roles.

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
    default role parser will also return compressed results.
    """

    def __init__(self, int_parser: typing.Optional[builtins_parsers.IntParser] = None):
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)

    async def loads(
        self,
        argument: str,
        *,
        source: typing.Union[
            parser_source.GuildAware,
            parser_source.MessageAware,
            parser_source.ChannelAware,
        ],
    ) -> disnake.Role:
        """Asynchronously load a role from a string.

        This uses the underlying :attr:`int_parser`.

        This method first tries to get the role from cache. If this fails,
        it will try to fetch the role instead.

        .. warning::
            This method can make API requests.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a role.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`guild <disnake.Guild>`, :class:`message <disnake.Message>`,
            or a :class:`channel <disnake.TextChannel>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A role with the id stored in the ``argument`` could not be found.

        """
        guild = parser_source.get_guild_from_source(source)
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

    def dumps(self, argument: disnake.Role) -> str:
        """Dump a role into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return self.int_parser.dumps(argument.id)
