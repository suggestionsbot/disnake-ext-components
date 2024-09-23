"""Interaction implementations extending disnake interactions."""

from __future__ import annotations

import functools
import typing

import disnake
from disnake.ext.components.api import component as component_api

__all__: typing.Sequence[str] = (
    "WrappedInteraction",
    "MessageInteraction",
    "CommandInteraction",
    "wrap_interaction",
    "wrap_interaction_for",
)


ComponentT = typing.TypeVar(
    "ComponentT",
    bound=typing.Union[component_api.RichComponent, disnake.ui.WrappedComponent],
)

Components = typing.Union[
    # ActionRow[ComponentT],
    ComponentT,
    typing.Sequence[
        typing.Union[
            # "ActionRow[ComponentT]",
            ComponentT,
            typing.Sequence[ComponentT],
        ]
    ],
]
# TODO: Custom action rows?

MessageComponents = typing.Union[
    component_api.RichButton,
    disnake.ui.Button[typing.Any],
    component_api.RichSelect,
    disnake.ui.StringSelect[typing.Any],
    disnake.ui.ChannelSelect[typing.Any],
    disnake.ui.RoleSelect[typing.Any],
    disnake.ui.UserSelect[typing.Any],
    disnake.ui.MentionableSelect[typing.Any],
]

P = typing.ParamSpec("P")
InteractionT = typing.TypeVar("InteractionT", bound=disnake.Interaction)
ReturnT = typing.TypeVar("ReturnT")

InteractionCallback = typing.Callable[
    typing.Concatenate[InteractionT, P],
    typing.Coroutine[None, None, ReturnT],
]
InteractionCallbackMethod = typing.Callable[
    typing.Concatenate[typing.Any, InteractionT, P],
    typing.Coroutine[None, None, ReturnT],
]

MISSING = disnake.utils.MISSING


async def _prepare(component: MessageComponents) -> disnake.ui.MessageUIComponent:
    if isinstance(
        component, (component_api.RichButton, component_api.RichSelect)
    ):  # TODO: add select
        return await component.as_ui_component()  # pyright: ignore[reportReturnType]

    return component


@typing.overload
async def _to_ui_components(
    components: Components[MessageComponents] = MISSING,
    *,
    allow_none: typing.Literal[False] = False,
) -> disnake.ui.Components[disnake.ui.MessageUIComponent]:
    ...


@typing.overload
async def _to_ui_components(
    components: typing.Optional[Components[MessageComponents]] = MISSING,
    *,
    allow_none: typing.Literal[True],
) -> typing.Optional[disnake.ui.Components[disnake.ui.MessageUIComponent]]:
    ...


async def _to_ui_components(
    components: typing.Optional[Components[MessageComponents]] = MISSING,
    *,
    allow_none: bool = False,
) -> typing.Optional[disnake.ui.Components[disnake.ui.MessageUIComponent]]:
    if components is None:
        if not allow_none:
            msg = "Components cannot be None in this method."
            raise TypeError(msg)
        return components

    if components is MISSING:
        return MISSING

    if not isinstance(components, typing.Sequence):
        return await _prepare(components)

    finalised: disnake.ui.Components[disnake.ui.MessageUIComponent] = []
    for component in components:
        if not isinstance(component, typing.Sequence):
            finalised.append(await _prepare(component))
            continue

        finalised.append([await _prepare(nested) for nested in component])

    return finalised


class WrappedInteraction(disnake.Interaction):
    """Interaction implementation that wraps :class:`disnake.Interaction`.

    This wrapped interaction class natively supports disnake-ext-components'
    specialised components classes and -- unlike vanilla disnake interactions --
    can send them without manually having to convert them to native disnake
    components first.

    Attribute access is simply proxied to the wrapped interaction object by
    means of a custom :meth:`__getattr__` implementation.
    """

    __slots__ = ("_wrapped",)

    def __init__(self, wrapped: disnake.Interaction):
        self._wrapped = wrapped

    def __getattr__(self, name: str) -> typing.Any:  # noqa: ANN401
        return getattr(self._wrapped, name)

    @disnake.utils.cached_slot_property("_cs_response")
    def response(self) -> WrappedInteractionResponse:
        """Returns an object responsible for handling responding to the interaction.

        A response can only be done once. If secondary messages need to be sent,
        consider using :attr:`followup` instead.
        """  # noqa: D401
        return WrappedInteractionResponse(super().response)

    @disnake.utils.cached_slot_property("_cs_followup")
    def followup(self) -> disnake.Webhook:
        """Returns the follow up webhook for follow up interactions."""  # noqa: D401
        return self._wrapped.followup  # TODO: custom followup object

    async def edit_original_response(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: PLR0913
        self,
        content: typing.Optional[str] = MISSING,
        *,
        embed: typing.Optional[disnake.Embed] = MISSING,
        embeds: typing.List[disnake.Embed] = MISSING,
        file: disnake.File = MISSING,
        files: typing.List[disnake.File] = MISSING,
        attachments: typing.Optional[typing.List[disnake.Attachment]] = MISSING,
        view: typing.Optional[disnake.ui.View] = MISSING,
        components: typing.Optional[Components[MessageComponents]] = MISSING,
        suppress_embeds: bool = MISSING,
        allowed_mentions: typing.Optional[disnake.AllowedMentions] = None,
    ) -> disnake.InteractionMessage:
        """Edit the original, previously sent interaction response message.

        This is a lower level interface to :meth:`InteractionMessage.edit` in
        case you do not want to fetch the message and save an HTTP request.

        This method is also the only way to edit the original response if
        the message sent was ephemeral.

        .. note::
            If the original response message has embeds with images that were created
            from local files (using the ``file`` parameter with :meth:`Embed.set_image`
            or :meth:`Embed.set_thumbnail`), those images will be removed if the
            message's attachments are edited in any way (i.e. by setting ``file``/
            ``files``/``attachments``, or adding an embed with local files).

        .. versionchanged:: 2.6

            This function was renamed from ``edit_original_message``.

        Parameters
        ----------
        content:
            The content to edit the message with, or :obj:``None`` to clear it.
        embed:
            The new embed to replace the original with. This cannot be mixed with the
            ``embeds`` parameter.
            Could be :obj:`None` to remove the embed.
        embeds:
            The new embeds to replace the original with. Must be a maximum of 10.
            This cannot be mixed with the ``embed`` parameter.
            To remove all embeds ``[]`` should be passed.
        file:
            The file to upload. This cannot be mixed with the ``files`` parameter.
            Files will be appended to the message, see the ``attachments`` parameter
            to remove/replace existing files.
        files:
            A list of files to upload. This cannot be mixed with the ``file`` parameter.
            Files will be appended to the message, see the ``attachments`` parameter
            to remove/replace existing files.
        attachments:
            A list of attachments to keep in the message.
            If ``[]`` or :obj:`None` is passed then all existing attachments are
            removed. Keeps existing attachments if not provided.

            .. versionadded:: 2.2

            .. versionchanged:: 2.5
                Supports passing ``None`` to clear attachments.

        view:
            The updated view to update this message with. This cannot be mixed with
            ``components``. If ``None`` is passed then the view is removed.
        components:
            A list of components to update this message with. This cannot be mixed with
            ``view``. If ``None`` is passed then the components are removed.

            .. versionadded:: 2.4

        allowed_mentions:
            Controls the mentions being processed in this message.
            See :meth:`.abc.Messageable.send` for more information.

        suppress_embeds:
            Whether to suppress embeds for the message. This hides
            all the embeds from the UI if set to ``True``. If set
            to ``False``, this brings the embeds back if they were
            suppressed.

            .. versionadded:: 2.7

        flags:
            The new flags to set for this message. Overrides existing flags.
            Only :attr:`~MessageFlags.suppress_embeds` is supported.

            If parameter ``suppress_embeds`` is provided,
            that will override the setting of :attr:`.MessageFlags.suppress_embeds`.

            .. versionadded:: 2.9

        Raises
        ------
        disnake.HTTPException
            Editing the message failed.
        disnake.Forbidden
            Edited a message that is not yours.
        TypeError
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``
        ValueError
            The length of ``embeds`` was invalid.

        Returns
        -------
        :class:`InteractionMessage`
            The newly edited message.

        """
        return await self._wrapped.edit_original_response(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            attachments=attachments,
            view=view,
            components=await _to_ui_components(components, allow_none=True),
            suppress_embeds=suppress_embeds,
            allowed_mentions=allowed_mentions,
        )

    edit_original_message = edit_original_response

    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: PLR0913, D102
        self,
        content: typing.Optional[str] = None,
        *,
        embed: disnake.Embed = MISSING,
        embeds: typing.List[disnake.Embed] = MISSING,
        file: disnake.File = MISSING,
        files: typing.List[disnake.File] = MISSING,
        allowed_mentions: disnake.AllowedMentions = MISSING,
        view: disnake.ui.View = MISSING,
        components: Components[MessageComponents] = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
        suppress_embeds: bool = False,
        delete_after: float = MISSING,
    ) -> None:
        # <<docstring inherited from disnake.Interaction>>

        return await self._wrapped.send(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            allowed_mentions=allowed_mentions,
            view=view,
            components=await _to_ui_components(components),
            tts=tts,
            ephemeral=ephemeral,
            suppress_embeds=suppress_embeds,
            delete_after=delete_after,
        )


class WrappedInteractionResponse(disnake.InteractionResponse):
    """Interaction response implementation that wraps :class:`disnake.InteractionResponse`.

    This wrapped interaction response class natively supports
    disnake-ext-components' specialised components classes and -- unlike
    vanilla disnake interactions -- can send them without manually having to
    convert them to native disnake components first.

    Attribute access is simply proxied to the wrapped interaction response
    object by means of a custom :meth:`__getattr__` implementation.
    """  # noqa: E501

    __slots__ = ("_wrapped",)

    def __init__(self, wrapped: disnake.InteractionResponse):
        self._wrapped = wrapped

    def __getattr__(self, name: str) -> typing.Any:  # noqa: ANN401
        """Get an attribute of this class or the wrapped interaction."""
        return getattr(self._wrapped, name)

    async def send_message(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: PLR0913
        self,
        content: typing.Optional[str] = None,
        *,
        embed: disnake.Embed = MISSING,
        embeds: typing.List[disnake.Embed] = MISSING,
        file: disnake.File = MISSING,
        files: typing.List[disnake.File] = MISSING,
        allowed_mentions: disnake.AllowedMentions = MISSING,
        view: disnake.ui.View = MISSING,
        components: Components[MessageComponents] = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
        suppress_embeds: bool = False,
        delete_after: float = MISSING,
    ) -> None:
        # <<docstring inherited from disnake.Interaction>>

        return await self._wrapped.send_message(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            allowed_mentions=allowed_mentions,
            view=view,
            components=await _to_ui_components(components),
            tts=tts,
            ephemeral=ephemeral,
            suppress_embeds=suppress_embeds,
            delete_after=delete_after,
        )

    async def edit_message(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: PLR0913
        self,
        content: typing.Optional[str] = None,
        *,
        embed: disnake.Embed = MISSING,
        embeds: typing.List[disnake.Embed] = MISSING,
        file: disnake.File = MISSING,
        files: typing.List[disnake.File] = MISSING,
        attachments: typing.Optional[typing.List[disnake.Attachment]] = MISSING,
        allowed_mentions: disnake.AllowedMentions = MISSING,
        view: disnake.ui.View = MISSING,
        components: typing.Optional[Components[MessageComponents]] = MISSING,
    ) -> None:
        # <<docstring inherited from disnake.Interaction>>

        return await self._wrapped.edit_message(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            attachments=attachments,
            allowed_mentions=allowed_mentions,
            view=view,
            components=await _to_ui_components(components, allow_none=True),
        )


class MessageInteraction(  # pyright: ignore[reportIncompatibleMethodOverride, reportIncompatibleVariableOverride]
    WrappedInteraction, disnake.MessageInteraction
):
    """Message interaction implementation that wraps :class:`disnake.MessageInteraction`.

    This wrapped message interaction class natively supports
    disnake-ext-components' specialised components classes and -- unlike
    vanilla disnake interactions -- can send them without manually having to
    convert them to native disnake components first.

    Attribute access is simply proxied to the wrapped message interaction
    object by means of a custom :meth:`__getattr__` implementation.
    """  # noqa: E501

    # __slots__ = ()  # No slots on disnake.MessageInteraction...

    def __init__(self, wrapped: disnake.MessageInteraction):
        self._wrapped = wrapped

    # message = proxy.ProxiedProperty("_wrapped")


class CommandInteraction(  # pyright: ignore[reportIncompatibleMethodOverride, reportIncompatibleVariableOverride]
    WrappedInteraction, disnake.CommandInteraction
):
    """Message interaction implementation that wraps :class:`disnake.CommandInteraction`.

    This wrapped command interaction class natively supports
    disnake-ext-components' specialised components classes and -- unlike
    vanilla disnake interactions -- can send them without manually having to
    convert them to native disnake components first.

    Attribute access is simply proxied to the wrapped command interaction
    object by means of a custom :meth:`__getattr__` implementation.
    """  # noqa: E501

    def __init__(self, wrapped: disnake.CommandInteraction):
        self._wrapped = wrapped


@typing.overload
def wrap_interaction(
    interaction: disnake.CommandInteraction,
) -> CommandInteraction:
    ...


@typing.overload
def wrap_interaction(
    interaction: disnake.MessageInteraction,
) -> MessageInteraction:
    ...


@typing.overload
def wrap_interaction(interaction: disnake.Interaction) -> WrappedInteraction:
    ...


def wrap_interaction(interaction: disnake.Interaction) -> WrappedInteraction:
    """Wrap a disnake interaction type for disnake-ext-components compatibility.

    Interactions wrapped in this way can send disnake-ext-components'
    specialised components directly, without having to first convert them to
    native disnake components.

    Parameters
    ----------
    interaction:
        The interaction to wrap.

    Returns
    -------
    WrappedInteraction:
        The wrapped interaction. Note that this can be any subclass of
        :class:`WrappedInteraction`:

        - Wrapping a (subclass of) :class:`disnake.MessageInteraction` returns
          a :class:`MessageInteraction`,
        - Wrapping a (subclass of) :class:`disnake.CommandInteraction` returns a
          :class:`CommandInteraction`,
        - Wrapping any other interaction class returns a
          :class:`WrappedInteraction`.

    """
    if isinstance(interaction, disnake.MessageInteraction):
        return MessageInteraction(interaction)

    # TODO: ModalInteraction

    return WrappedInteraction(interaction)


def wrap_args_kwargs(
    args: typing.Tuple[object, ...], kwargs: typing.Dict[str, object]
) -> typing.Tuple[typing.Tuple[object, ...], typing.Dict[str, object]]:
    args_iter = iter(args)
    new_args: typing.List[object] = []

    # We assume there's only ever going to be one interaction that needs to be
    # wrapped. We check args first, and if no interaction was found, we check
    # kwargs. Note that we only check at most two args.
    for arg, _ in zip(args_iter, range(2)):
        if isinstance(arg, disnake.Interaction):
            new_args.append(wrap_interaction(arg))
            break
        else:
            new_args.append(arg)

    else:
        for kw, arg in kwargs.items():
            if isinstance(arg, disnake.Interaction):
                kwargs[kw] = wrap_interaction(arg)
                break

        else:
            msg = "No wrappable interaction was found!"
            raise TypeError(msg)

    new_args.extend(args_iter)

    return tuple(new_args), kwargs


@typing.overload
def wrap_interaction_for(
    callback: InteractionCallbackMethod[WrappedInteraction, P, ReturnT]
) -> InteractionCallbackMethod[disnake.Interaction, P, ReturnT]:
    ...


@typing.overload
def wrap_interaction_for(
    callback: InteractionCallbackMethod[MessageInteraction, P, ReturnT]
) -> InteractionCallbackMethod[disnake.MessageInteraction, P, ReturnT]:
    ...


@typing.overload
def wrap_interaction_for(
    callback: InteractionCallbackMethod[CommandInteraction, P, ReturnT]
) -> InteractionCallbackMethod[disnake.CommandInteraction, P, ReturnT]:
    ...


@typing.overload
def wrap_interaction_for(
    callback: InteractionCallback[WrappedInteraction, P, ReturnT]
) -> InteractionCallback[disnake.Interaction, P, ReturnT]:
    ...


@typing.overload
def wrap_interaction_for(
    callback: InteractionCallback[MessageInteraction, P, ReturnT]
) -> InteractionCallback[disnake.MessageInteraction, P, ReturnT]:
    ...


@typing.overload
def wrap_interaction_for(
    callback: InteractionCallback[CommandInteraction, P, ReturnT]
) -> InteractionCallback[disnake.CommandInteraction, P, ReturnT]:
    ...


def wrap_interaction_for(
    callback: typing.Callable[..., typing.Coroutine[None, None, ReturnT]]
) -> typing.Callable[..., typing.Coroutine[None, None, ReturnT]]:
    """Wrap a callback that takes an interaction for disnake-ext-components compatibility.

    Interactions wrapped in this way can send disnake-ext-components'
    specialised components directly, without having to first convert them to
    native disnake components.

    .. see-also::
        This uses :func:`wrap_interaction` under the hood.

    Parameters
    ----------
    callback:
        The callback to wrap.

        This can be either a function or a method. In case of a function, the
        interaction must be the first argument. Otherwise, it must be the
        second argument after ``self``.

    Returns
    -------
    :class:`typing.Callable`[..., :class:`typing.Any`]
        The callback that had its interaction wrapped.

    """  # noqa: E501

    @functools.wraps(callback)
    async def wrapper(*args: object, **kwargs: object) -> ReturnT:
        args, kwargs = wrap_args_kwargs(args, kwargs)
        return await callback(*args, **kwargs)

    return wrapper
