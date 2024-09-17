"""Parser implementation for disnake invite types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import helpers

__all__: typing.Sequence[str] = ("InviteParser",)


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
