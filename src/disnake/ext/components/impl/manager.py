"""Default implementation of the component manager api."""

from __future__ import annotations

import contextlib
import enum
import logging
import sys
import typing
import weakref

import attr
import disnake
from disnake.ext import commands
from disnake.ext.components import interaction as interaction_impl
from disnake.ext.components.api import component as component_api

if typing.TYPE_CHECKING:
    import typing_extensions

__all__: typing.Sequence[str] = ("ComponentManager", "get_manager")


_LOGGER = logging.getLogger(__name__)
_ROOT = sys.intern("root")
_COMPONENT_EVENT = sys.intern("on_message_interaction")
_MODAL_EVENT = sys.intern("on_modal_submit")


T = typing.TypeVar("T")

AnyBot = typing.Union[commands.Bot, commands.InteractionBot]

CallbackWrapperFunc = typing.Callable[
    ["ComponentManager", component_api.RichComponent, disnake.Interaction],
    typing.AsyncGenerator[None, None],
]
CallbackWrapper = typing.Callable[
    ["ComponentManager", component_api.RichComponent, disnake.Interaction],
    typing.AsyncContextManager[None],
]
CallbackWrapperFuncT = typing.TypeVar("CallbackWrapperFuncT", bound=CallbackWrapperFunc)


ExceptionHandlerFunc = typing.Callable[
    ["ComponentManager", component_api.RichComponent, disnake.Interaction, Exception],
    typing.Coroutine[typing.Any, typing.Any, typing.Optional[bool]],
]
ExceptionHandlerFuncT = typing.TypeVar(
    "ExceptionHandlerFuncT", bound=ExceptionHandlerFunc
)

ComponentType = typing.Type[component_api.RichComponent]
ComponentTypeT = typing.TypeVar("ComponentTypeT", bound=ComponentType)


class NotSetType(enum.Enum):
    """Typehint for sentinel value."""

    NotSet = enum.auto()
    """Sentinel value to distinguish whether or not None was explicitly passed."""


NotSet = NotSetType.NotSet
"""Sentinel value to distinguish whether or not None was explicitly passed."""


NotSetNoneOr = typing.Union[typing.Literal[NotSet], None, T]


def _is_set(obj: NotSetNoneOr[T]) -> typing_extensions.TypeGuard[typing.Optional[T]]:
    return obj is not NotSet


def _minimise_count(count: int) -> str:
    # We only need to support counts up to 25, as that is the
    # maximum number of components that can go on a message.
    # Byte-length 1 should support a range of 0~255 inclusive.
    byte = count.to_bytes(1, "little")
    # Decode into a charset that supports these bytes as a single char.
    return byte.decode("latin-1")


_COUNT_CHARS: typing.Final[typing.Tuple[str, ...]] = tuple(
    map(_minimise_count, range(25))
)
_DEFAULT_SEP: typing.Final[str] = sys.intern("|")
_DEFAULT_COUNT: typing.Final[typing.Literal[True]] = True


@contextlib.asynccontextmanager
async def default_callback_wrapper(
    manager: component_api.ComponentManager,  # noqa: ARG001
    component: component_api.RichComponent,  # noqa: ARG001
    interaction: disnake.Interaction,  # noqa: ARG001
) -> typing.AsyncGenerator[None, None]:
    """Wrap a callback for a component manager.

    This is the default implementation, and is effectively a no-op.
    """
    yield


async def default_exception_handler(
    manager: component_api.ComponentManager,
    component: component_api.RichComponent,
    interaction: disnake.Interaction,  # noqa: ARG001
    exception: Exception,
) -> bool:
    """Handle an exception that occurs during execution of a component callback.

    This is the default implementation, and simply passes the exception down.
    If it is passed down to the root logger, and the root logger also has this
    default implementation, the exception is logged.
    """
    if manager.name is not _ROOT:
        # Not the root manager, try passing down.
        return False

    # We're at the root logger, and the exception remains unhandled. Log it.

    exc_info = (
        type(exception),
        exception,
        exception.__traceback__.tb_next if exception.__traceback__ else None,
    )

    _LOGGER.exception(
        "An exception was caught on manager %r while handling the callback of"
        " component %r, registered to manager %r:",
        manager.name,
        component,
        component.manager.name if component.manager else "<unknown>",
        exc_info=exc_info,
    )

    return True


@attr.define
class _ModuleData:
    name: str
    id: int

    @classmethod
    def from_object(cls, obj: object) -> typing_extensions.Self:
        module = sys.modules[obj.__module__]
        return cls(obj.__module__, id(module))

    def is_active(self) -> bool:
        if self.name not in sys.modules:
            return False

        return self.id == id(sys.modules[self.name])

    def is_reload_of(self, other: typing_extensions.Self) -> bool:
        return self.name == other.name and self.id != other.id


class ComponentManager(component_api.ComponentManager):
    """The standard implementation of a component manager.

    Component managers keep track of disnake-ext-components' special components
    and ensure they smoothly communicate with disnake's bots. Since this relies
    on listener functionality, component managers are incompatible with
    :class:`disnake.Client`-classes.

    To register a component to a component manager, use :meth:`register`.
    Without registering your components, they will remain unresponsive.

    To get an instance of a component manager, use :func:`get_manager`. This
    will automatically create missing managers if needed, much like
    :func:`logging.getLogger`. Similarly, managers feature a parent-child
    hierarchy in the same way loggers do. For example, a manager named
    "foo.bar" would be a child of the manager named "foo". When a component is
    invoked on a child, it will wrap the callback using the callback wrappers
    of all of its parents. Similarly, if an exception occurs, the exception
    handlers of all parents can be tried until the error was handled
    successfully.
    """

    __slots__: typing.Sequence[str] = (
        "_name",
        "_children",
        "_components",
        "_count",
        "_counter",
        "_module_data",
        "_sep",
        "wrap_callback",
        "handle_exception",
    )

    _name: str
    _children: typing.Set[ComponentManager]
    _components: weakref.WeakValueDictionary[str, ComponentType]
    _count: typing.Optional[bool]
    _counter: int
    _module_data: typing.Dict[str, _ModuleData]
    _sep: typing.Optional[str]

    def __init__(
        self,
        name: str,
        *,
        count: typing.Optional[bool] = None,
        sep: typing.Optional[str] = None,
    ):
        self._name = name
        self._children = set()
        self._components = weakref.WeakValueDictionary()
        self._count = count
        self._counter = 0
        self._module_data = {}
        self._sep = sep
        self.wrap_callback: CallbackWrapper = default_callback_wrapper
        self.handle_exception: ExceptionHandlerFunc = default_exception_handler

    def __repr__(self) -> str:
        return f"ComponentManager(name={self.name})"

    @property
    def name(self) -> str:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return self._name

    @property
    def children(self) -> typing.Set[ComponentManager]:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return self._children

    @property
    def components(self) -> typing.Mapping[str, ComponentType]:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return self._components

    @property
    def count(self) -> bool:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return _recurse_parents_getattr(self, "_count", _DEFAULT_COUNT)

    @property
    def counter(self) -> int:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return self._counter

    @property
    def sep(self) -> str:
        """The separator used to delimit parts of the custom ids of this manager."""
        return _recurse_parents_getattr(self, "_sep", _DEFAULT_SEP)

    @property
    def parent(self) -> typing.Optional[typing_extensions.Self]:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        if "." not in self.name:
            # Return the root manager if this is not the root manager already.
            return None if self.name is _ROOT else get_manager(_ROOT)

        root, _ = self.name.rsplit(".", 1)
        return get_manager(root)

    def config(
        self, count: NotSetNoneOr[bool] = NotSet, sep: NotSetNoneOr[str] = NotSet
    ) -> None:
        """Set configuration options on this manager."""
        if _is_set(count):
            self._count = count

        if _is_set(sep):
            self._sep = sep

    def make_identifier(self, component_type: ComponentType) -> str:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return component_type.__name__

    def get_identifier(  # noqa: D102
        self, custom_id: str
    ) -> typing.Tuple[str, typing.Sequence[str]]:
        # <<docstring inherited from api.components.ComponentManager>>

        name, *params = custom_id.split(self.sep)

        if self.count and name.endswith(_COUNT_CHARS):
            # Count is always the single last character in the name part.
            return name[:-1], params

        return name, params

    def increment(self) -> str:  # noqa: D102
        count = _minimise_count(self.count)

        self._counter += 1
        if self._counter > 24:
            self._counter = 0

        return count

    async def make_custom_id(  # noqa: D102
        self, component: component_api.RichComponent
    ) -> str:
        # <<docstring inherited from api.components.ComponentManager>>

        identifier = self.make_identifier(type(component))

        if self.count:
            identifier = identifier + self.increment()

        dumped_params = await component.factory.dump_params(component)

        return self.sep.join([identifier, *dumped_params.values()])

    async def parse_interaction(  # noqa: D102
        self, interaction: disnake.Interaction
    ) -> typing.Optional[component_api.RichComponent]:
        # <<docstring inherited from api.components.ComponentManager>>

        custom_id = interaction.data["custom_id"]
        identifier, params = self.get_identifier(custom_id)

        if identifier not in self._components:
            return None

        component_type = self._components[identifier]
        module_data = self._module_data[identifier]

        if not module_data.is_active():
            # NOTE: This occurs if:
            #       - The module on which the component is defined was unloaded.
            #       - The module on which the component is defined was reloaded
            #         and the component was never overwritten. It could either
            #         have been removed, or simply no longer be registered. The
            #         component *should* therefore be unresponsive.
            #
            #       Since we do not want to fire components that (to the user)
            #       do not exist anymore, we should remove them from the
            #       manager and return None.
            self.deregister(component_type)
            return None

        return await component_type.factory.build_from_interaction(interaction, params)

    def register(self, component_type: ComponentTypeT) -> ComponentTypeT:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        identifier = self.make_identifier(component_type)
        module_data = _ModuleData.from_object(component_type)

        root_manager = get_manager(_ROOT)

        if identifier in root_manager._components:
            # NOTE: This occurs when a component is registered while another
            #       component with the same identifier already exists.
            #
            #       We now have two options:
            #       - This is caused by a reload. In this case, we expect the
            #         module name to remain unchanged and the module id to have
            #         changed. We can safely overwrite the old component.
            #       - This is an actual user error. If we were to silently
            #         overwrite the old component, it would unexpectedly go
            #         unresponsive. Instead, we raise an exception to the user.
            old_module_data = root_manager._module_data[identifier]
            if not module_data.is_reload_of(old_module_data):
                message = (
                    "Cannot register component with duplicate identifier"
                    f" {identifier!r}. (Original defined in module"
                    f" {old_module_data.name!r}, duplicate defined in module"
                    f" {module_data.name!r})"
                )
                raise RuntimeError(message)

        # Register to current manager and all parent managers.
        component_type.manager = self

        for manager in _recurse_parents(self):
            manager._components[identifier] = component_type
            manager._module_data[identifier] = module_data

        return component_type

    def deregister(  # noqa: D102
        self,
        component_type: ComponentType,
    ) -> None:
        # <<docstring inherited from api.components.ComponentManager>>

        identifier = self.make_identifier(component_type)
        component = self._components[identifier]

        if not component.manager:
            message = (
                f"Component {component_type.__name__!r} is not registered to a"
                " component manager."
            )
            raise TypeError(message)

        if not isinstance(component.manager, ComponentManager):
            # This should honestly never happen unless the user does some
            # really weird stuff.
            # TODO: Maybe think of an error message for this.
            raise TypeError

        # Deregister from the current manager and all parent managers.
        for manager in _recurse_parents(component.manager):
            manager._components.pop(identifier)
            manager._module_data.pop(identifier)

    def add_to_bot(self, bot: AnyBot) -> None:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        # Ensure we don't duplicate the listeners.
        if (
            self.invoke in bot.extra_events.get(_COMPONENT_EVENT, [])
            or self.invoke in bot.extra_events.get(_MODAL_EVENT, [])
        ):  # fmt: skip
            message = "This component manager is already registered to this bot."
            raise RuntimeError(message)

        bot.add_listener(self.invoke, _COMPONENT_EVENT)
        bot.add_listener(self.invoke, _MODAL_EVENT)

    def remove_from_bot(self, bot: AnyBot) -> None:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        # Bot.remove_listener silently ignores if the event doesn't exist,
        # so we manually handle raising an exception for it.
        if not (
            self.invoke in bot.extra_events.get(_COMPONENT_EVENT, [])
            and self.invoke in bot.extra_events.get(_MODAL_EVENT, [])
        ):
            message = "This component manager is not yet registered to this bot."
            raise RuntimeError(message)

        bot.remove_listener(self.invoke, _COMPONENT_EVENT)
        bot.remove_listener(self.invoke, _MODAL_EVENT)

    def as_callback_wrapper(self, func: CallbackWrapperFuncT) -> CallbackWrapperFuncT:
        """Register a callback as this managers' callback wrapper.

        By default, this is essentially a no-op.

        A callback wrapper MUST be an async function with ONE yield statement.
        - Any code before the yield statement is run before the component
        callback is invoked,
        - The component is invoked at the yield statement,
        - Any code after the yield statement is run after the component
        callback is invoked. This can be used for cleanup.

        It is therefore also possible to use context managers over the yield
        statement, to automatically handle resource management.

        In case this manager has a parent manager, the parent's callback
        wrapper will be used first, starting all the way at the root manager.
        For example, on a manager named "foo.bar", the callback will first be
        wrapped by the root manager, then by "foo", then by "foo.bar", and only
        then will the component callback finally be invoked.

        Note that any exceptions raised in any callback wrapper will cancel any
        other active callback wrappers and propagate the exception to the
        manager's error handler.

        Examples
        --------
        .. code-block:: python3
            manager = get_manager()


            @manager.as_callback_wrapper
            async def wrapper(component, interaction):
                print(f"User {inter.author.name} invoked {type(component).__name__}.)
                yield
                print(f"Successfully ran callback for {type(component).__name__}.)

        Parameters
        ----------
        func: Callable[[:class:`ComponentManager`, :class:`RichComponent`, :class:`disnake.Interaction`], AsyncGenerator[None, None]]
            The callback to register. This must be an async function that takes
            the component manager as the first argument, the component as the
            second argument, and the interaction as the last. The function must
            have a single ``yield``-statement that yields ``None``.

        Returns
        -------
        Callable[[:class:`RichComponent`, :class:`disnake.Interaction`], AsyncGenerator[None, None]]
            The function that was just registered.
        """  # noqa: E501
        self.wrap_callback = contextlib.asynccontextmanager(func)
        return func

    def as_exception_handler(
        self, func: ExceptionHandlerFuncT
    ) -> ExceptionHandlerFuncT:
        """Register a callback as this managers' error handler.

        By default, this simply logs the exception and keeps it from
        propagating.

        An error handler should return a boolean or ``None``:
        - ``True`` if the error was successfully handled and should not be
        propagated further.
        - ``False`` or ``None`` if the error was *not* successfully handled and
        should be passed to the next error handler in line.

        Note that it is therefore also possible to use context managers over
        the yield statement.

        In case this manager has a parent manager, the parent's error handler
        will be used if this one returns ``False`` or ``None``. For example,
        of a manager named "foo.bar", any exceptions will first be handled by
        "foo.bar", if that fails it will be handled by "foo", and finally if
        that also fails it will be handled by the root handler.

        Examples
        --------
        .. code-block:: python3
            manager = get_manager()


            @manager.as_exception_handler
            async def wrapper(component, interaction, exception):
                if isinstance(exception, TypeError):
                    return True  # Silently ignore any TypeErrors

                return False  # Propagate all other errors.

        Parameters
        ----------
        func: Callable[[:class:`ComponentManager`, :class:`RichComponent`, :class:`disnake.Interaction`, :class:`Exception`], None]
            The callback to register. This must be an async function that takes
            the component manager as the first argument, the component as the
            second, the interaction as the third, and the exception as the last.
            The function must return ``True`` to indicate that the error was
            handled successfully, or either ``False`` or ``None`` to indicate
            the opposite.

        Returns
        -------
        Callable[[:class:`RichComponent`, :class:`disnake.Interaction`, :class:`Exception`], None]
            The function that was just registered.
        """  # noqa: E501
        self.handle_exception = func
        return func

    async def invoke(self, interaction: disnake.Interaction) -> None:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        # First, we check if the component is managed.
        component = await self.parse_interaction(interaction)
        if not (component and component.manager):
            # If the component was found, the manager is guaranteed to be
            # defined but we need the extra check for type-safety.
            return

        if not isinstance(component.manager, ComponentManager):
            # This should honestly never happen unless the user does some
            # really weird stuff.
            # TODO: Maybe think of an error message for this.
            raise TypeError

        # We traverse the managers in reverse: root first, then child, etc.
        # until we reach the component's actual manager. Therefore, we first
        # store all managers in a list, so that we can call reversed() on it
        # later.
        # This applies only to the callback wrappers. Error handlers are called
        # starting from the actual manager and propagated down to the root
        # manager if the error was left unhandled.
        managers = list(_recurse_parents(component.manager))

        try:
            async with contextlib.AsyncExitStack() as stack:
                # Enter all the context managers...
                for manager in reversed(managers):
                    await stack.enter_async_context(
                        manager.wrap_callback(manager, component, interaction)
                    )

                # If none raised, we run the callback.
                wrapped = interaction_impl.wrap_interaction(interaction)
                await component.callback(wrapped)

        except Exception as exception:  # noqa: BLE001
            # Blanket exception catching is desired here as it's meant to
            # redirect all non-system errors to the error handler.

            for manager in managers:
                if await manager.handle_exception(
                    manager, component, interaction, exception
                ):
                    # If an error handler returns True, consider the error
                    # handled and skip the remaining handlers.
                    break


_MANAGER_STORE: typing.Final[typing.Dict[str, ComponentManager]] = {}


def _recurse_parents(manager: ComponentManager) -> typing.Iterator[ComponentManager]:
    yield manager
    while manager := manager.parent:  # pyright: ignore
        yield manager


def _recurse_parents_getattr(
    manager: ComponentManager, attribute: str, default: T
) -> T:
    for parent in _recurse_parents(manager):
        value = getattr(parent, attribute)
        if value is not None:
            return value

    return default


def get_manager(name: typing.Optional[str] = None) -> ComponentManager:
    """Get a manager by name, or create one if it does not yet exist.

    Managers follow a parent-child hierarchy. For example, a manager "foo.bar"
    would be a child of "foo". Any components registered to "foo.bar" would
    also
    """
    if name is None:
        # TODO: Maybe use a sentinel:
        #       - auto-infer name if sentinel,
        #       - return root logger if None was passed explicitly.
        name = _ROOT

    if name in _MANAGER_STORE:
        return _MANAGER_STORE[name]

    _MANAGER_STORE[name] = manager = ComponentManager(name)

    if "." in name:
        root, _ = name.rsplit(".", 1)
        parent = get_manager(root)
        parent.children.add(manager)

    return manager
