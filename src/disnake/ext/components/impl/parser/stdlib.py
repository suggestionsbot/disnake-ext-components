"""Parser implementations for types provided in the python standard library."""

from __future__ import annotations

import contextlib
import datetime
import enum
import inspect
import string
import typing

import disnake.utils
import typing_extensions
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.internal import aio

if typing.TYPE_CHECKING:
    import disnake

__all__: typing.Sequence[str] = (
    "FloatParser",
    "IntParser",
    "BoolParser",
    "StringParser",
    "DatetimeParser",
    "DateParser",
    "TimeParser",
    "TimedeltaParser",
    "TimezoneParser",
    "CollectionParser",
    "TupleParser",
    "UnionParser",
)

_NoneType: typing.Type[None] = type(None)
_NONES = (None, _NoneType)
_INT_CHARS = string.digits + string.ascii_lowercase

_NumberT = typing_extensions.TypeVar("_NumberT", bound=float, default=float)
_CollectionT = typing_extensions.TypeVar(  # Simplest iterable container object.
    "_CollectionT", bound=typing.Collection[object], default=typing.Collection[str]
)
_TupleT = typing_extensions.TypeVar("_TupleT", bound=typing.Tuple[typing.Any, ...])
_T = typing_extensions.TypeVar("_T")

# NONE


@parser_base.register_parser_for(_NoneType)
class NoneParser(parser_base.Parser[None]):
    r"""Parser implementation for :obj:`None`.

    Mainly relevant for :obj:`~typing.Optional`\[...] parsers.

    Parameters
    ----------
    strict: bool
        Whether this parser should be set to :attr:`strict` mode.

        To prevent unforeseen bugs, this defaults to :obj:`True`.

    """

    strict: bool
    """Whether this parser is set to strict mode.

    See :meth:`loads` and :meth:`dumps` for the implications of strict-mode.
    """

    def __init__(self, *, strict: bool = True) -> None:
        self.strict = strict

    def loads(self, argument: str, /) -> None:
        """Load ``None`` from a string.

        If :attr:`strict` is set to ``True``, this will fail if the
        provided ``argument`` isn't the empty string (``""``). Otherwise,
        this parser will *always* return ``None``.

        Parameters
        ----------
        argument:
            The string that is to be converted to ``None``.

        Raises
        ------
        ValueError:
            The parser is in strict mode, and the provided ``argument`` was not
            the empty string.

        """
        if not argument or not self.strict:
            return None  # noqa: RET501

        msg = f"Strict `NoneParser`s can only load the empty string, got {argument!r}."
        raise ValueError(msg)

    def dumps(self, argument: None) -> str:
        """Dump ``None`` into a string.

        If :attr:`strict` is set to ``True``, this will fail if the
        provided ``argument`` isn't exactly ``None``. Otherwise,
        this parser will *always* return ``None``.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        Raises
        ------
        ValueError:
            The parser is in strict mode, and the provided ``argument`` was not
            ``None``.

        """
        if argument is None or not self.strict:
            return ""

        msg = f"Strict `NoneParser`s can only dump `None`, got {argument!r}."
        raise ValueError(msg)


# INT / FLOAT


def _removesuffix(string: str, suffix: str) -> str:
    return string[: -len(suffix) if string.endswith(suffix) else None]


def dumps_float(number: float) -> str:
    """Dump a float to a string.

    Ensures trailing .0 are stripped to minimise float character length.
    """
    return _removesuffix(str(number), ".0")


# TODO: decimal.Decimal parser for decimal numbers with set precision?


@parser_base.register_parser_for(float)
class FloatParser(parser_base.Parser[float]):
    r"""Parser implementation for :class:`float`\s."""

    def loads(self, argument: str) -> float:
        """Load a floating point number from a string.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a floating point number.

        """
        return float(argument)

    def dumps(self, argument: float) -> str:
        """Dump a floating point number into a string.

        Strips trailing ".0" where possible.

        Parameters
        ----------
        argument:
            The string that is to be converted into a floating point number.

        """
        return dumps_float(argument)


@parser_base.register_parser_for(int)
class IntParser(parser_base.Parser[int]):
    r"""Parser implementation for :class:`int`\s.

    Parameters
    ----------
    signed:
        Whether the parser supports signed integers.
        Defaults to ``True``.
    base:
        The base to use to use for storing integers.
        This is limited to ``2 <= base <= 36``.
        Defaults to ``36``.

    """

    signed: bool
    """Whether the parser supports signed integers."""
    base: int
    """The base to use to use for storing integers.
    This is limited to ``2 <= base <= 36`` as this is the range supported by
    python's :class:`int` constructor.

    If a greater base is required, a custom integer parser will have to be
    implemented.
    """

    def __init__(
        self,
        *,
        signed: bool = True,
        base: int = 36,
    ):
        if not 2 <= base <= 36:
            msg = "Base must be between 2 and 36."
            raise ValueError(msg)

        self.signed = signed
        self.base = base

    def loads(self, argument: str) -> int:
        r"""Load an integer from a string.

        Parameters
        ----------
        argument:
            The string that is to be converted to an ``int``.

        Raises
        ------
        ValueError:
            The parser has :attr:`signed` set to ``False`` but the argument
            was a negative number.
            Alternatively, the provided argument is not a valid integer at all.

        """
        result = int(argument, self.base)
        if not self.signed and result < 0:
            msg = "Unsigned numbers cannot be < 0."
            raise ValueError(msg)

        return result

    def dumps(self, argument: int) -> str:
        """Dump an integer into a string.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        # Try to short-circuit as much as possible
        if argument < self.base:
            return str(argument)
        if self.base == 2:
            return f"{argument:b}"
        if self.base == 8:
            return f"{argument:o}"
        if self.base == 10:
            return str(argument)
        if self.base == 16:
            return f"{argument:x}"

        # Can't short-circuit, convert to string manually.
        digits: typing.List[int] = []
        while argument:
            digits.append(argument % self.base)
            argument //= self.base

        return "".join(_INT_CHARS[d] for d in reversed(digits))


# BOOL

_DEFAULT_TRUES = frozenset(["true", "t", "yes", "y", "1"])
_DEFAULT_FALSES = frozenset(["false", "f", "no", "n", "0"])


@parser_base.register_parser_for(bool)
class BoolParser(parser_base.Parser[bool]):
    """Parser type with support for bools.

    This parser type can be supplied with a collection of strings for the
    values that should be considered true and false. By default,
    ``"true", "t", "yes", "y", "1"`` are considered ``True``, while
    ``"false", "f", "no", "n", "0"`` are considered ``False``. Note that this
    is case-insensitive.

    Parameters
    ----------
    trues:
        Values that should be considered ``True`` by this parser.
    falses:
        Values that should be considered ``False`` by this parser.

    """

    trues: typing.Collection[str]
    """A collection of values that should be considered ``True`` by this parser."""
    falses: typing.Collection[str]
    """A collection of values that should be considered ``False`` by this parser."""

    def __init__(
        self,
        trues: typing.Optional[typing.Collection[str]] = None,
        falses: typing.Optional[typing.Collection[str]] = None,
    ):
        self.trues = _DEFAULT_TRUES if trues is None else trues
        self.falses = _DEFAULT_FALSES if falses is None else falses

    def loads(self, argument: str) -> bool:
        """Load a boolean from a string.

        Parameters
        ----------
        argument:
            The string that is to be converted into a boolean.

        Raises
        ------
        ValueError:
            The string is not in :attr:`trues` or :attr:`falses`.

        """
        if argument in self.trues:
            return True
        elif argument in self.falses:
            return False

        trues_str = ", ".join(map(repr, self.trues))
        falses_str = ", ".join(map(repr, self.falses))
        msg = (
            f"Failed to parse {argument!r} into a bool. Expected any of"
            f" {trues_str} for True, or any of {falses_str} for False."
        )
        raise ValueError(msg)

    def dumps(self, argument: bool) -> str:  # noqa: FBT001
        """Dump a boolean into a string.

        By default, this opts to dump as ``"1"`` for ``True`` or ``"0"`` for
        ``False`` to only use one character's worth of space from the custom id.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        # NOTE: FBT001: Boolean trap is not relevant here, we're quite
        #               literally just dealing with a boolean.

        return "1" if argument else "0"


# STRING


@parser_base.register_parser_for(str)
class StringParser(parser_base.Parser[str]):
    """Parser type with support for strings.

    Both loads and dumps are essentially no-ops.
    """

    def loads(self, argument: str) -> str:
        """Load a string from a string.

        Parameters
        ----------
        argument:
            The string that is to be converted into a string.

        """
        return argument

    def dumps(self, argument: str) -> str:
        """Dump a string into a string.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return argument


# DATETIME


class _Resolution(int, enum.Enum):
    """The resolution with which datetimes are stored."""

    MICROS = 1e-6
    SECONDS = 1
    MINUTES = 60 * SECONDS
    HOURS = 60 * MINUTES
    DAYS = 24 * HOURS


# TODO: Is forcing the use of timezones on users really a parser_based move?
#       Probably.
@parser_base.register_parser_for(datetime.datetime)
class DatetimeParser(parser_base.Parser[datetime.datetime]):
    """Parser type with support for datetimes.

    Parameters
    ----------
    resolution:
        Dictates in how much detail the datetimes are stored inside strings.
        For example, a datetime object stored with resolution
        :attr:`DatetimeParser.res.DAYS` does not contain any information about
        hours/seconds/milliseconds/microseconds. Defaults to
        :attr:`DatetimeParser.res.SECONDS`.
    timezone:
        The timezone to use for parsing. Timezones returned by :meth:`loads`
        will always be of this timezone, and :meth:`dumps` will only accept
        datetimes of this timezone. Defaults to :obj:`datetime.timezone.utc`.

    """

    res = _Resolution

    def __init__(
        self,
        *,
        resolution: int = _Resolution.SECONDS,
        timezone: datetime.timezone = datetime.timezone.utc,
    ):
        self.resolution = resolution
        self.timezone = timezone

    def loads(self, argument: str) -> datetime.datetime:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return datetime.datetime.fromtimestamp(float(argument), tz=self.timezone)

    def dumps(self, argument: datetime.datetime) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>
        if argument.tzinfo != self.timezone:
            msg = (
                "Cannot dump the provided datetime object due to a mismatch in"
                f" timezones. (expected: {self.timezone}, got: {argument.tzinfo})"
            )
            raise RuntimeError(msg)

        timestamp = argument.timestamp()
        if self.resolution == _Resolution.MICROS:
            return str(timestamp)

        return str(int(timestamp // self.resolution) * self.resolution)


@parser_base.register_parser_for(datetime.date)
class DateParser(parser_base.Parser[datetime.date]):  # noqa: D101
    def loads(self, argument: str) -> datetime.date:  # noqa: D102
        return datetime.date.fromordinal(int(argument))

    def dumps(self, argument: datetime.date) -> str:  # noqa: D102
        return str(datetime.date.toordinal(argument))


@parser_base.register_parser_for(datetime.time)
class TimeParser(parser_base.Parser[datetime.time]):  # noqa: D101
    def loads(self, argument: str) -> datetime.time:  # noqa: D102
        return datetime.time.fromisoformat(argument)

    def dumps(self, argument: datetime.time) -> str:  # noqa: D102
        return datetime.time.isoformat(argument)


@parser_base.register_parser_for(datetime.timedelta)
class TimedeltaParser(parser_base.Parser[datetime.timedelta]):  # noqa: D101
    float_parser: FloatParser

    def __init__(self, float_parser: typing.Optional[FloatParser] = None):
        self.float_parser = float_parser or FloatParser()

    def loads(self, argument: str) -> datetime.timedelta:  # noqa: D102
        return datetime.timedelta(seconds=self.float_parser.loads(argument))

    def dumps(self, argument: datetime.timedelta) -> str:  # noqa: D102
        return self.float_parser.dumps(argument.total_seconds())


# NOTE: I assume seconds resolution for timezones is more than enough.
#       I would honestly assume even minutes are enough, though they
#       technically support going all the way down to microseconds.
@parser_base.register_parser_for(datetime.timezone)
class TimezoneParser(parser_base.Parser[datetime.timezone]):  # noqa: D101
    timedelta_parser: TimedeltaParser

    def __init__(self, timedelta_parser: typing.Optional[TimedeltaParser] = None):
        self.timedelta_parser = timedelta_parser or TimedeltaParser()

    def loads(self, argument: str) -> datetime.timezone:  # noqa: D102
        return datetime.timezone(self.timedelta_parser.loads(argument))

    def dumps(self, argument: datetime.timezone) -> str:  # noqa: D102
        return self.timedelta_parser.dumps(argument.utcoffset(None))


def _resolve_collection(type_: typing.Type[_CollectionT]) -> typing.Type[_CollectionT]:
    # ContainerParser itself does not support tuples.
    if issubclass(type_, typing.Tuple):
        msg = (
            f"{CollectionParser.__name__}s do not support tuples. Please use a "
            f"{TupleParser.__name__} instead."
        )
        raise TypeError(msg)

    if not typing_extensions.is_protocol(type_) and not inspect.isabstract(type_):
        # Concrete type, return as-is.
        return type_

    # Try to resolve an abstract type to a valid concrete structural subtype.
    if issubclass(type_, typing.Sequence):
        return typing.cast(typing.Type[_CollectionT], list)

    elif issubclass(type_, typing.AbstractSet):
        return typing.cast(typing.Type[_CollectionT], set)

    msg = f"Cannot infer a concrete type for abstract type {type_.__name__!r}."
    raise TypeError(msg)


# NOTE: TupleParser *must* be registered before CollectionParser!


@parser_base.register_parser_for(tuple)
class TupleParser(parser_base.SourcedParser[_TupleT]):
    """Parser type with support for tuples.

    The benefit of a tuple parser is fixed-length checks and the ability to set
    multiple types. For example, a ``Tuple[str, int, bool]`` parser will
    actually return a tuple with a ``str``, ``int``, and ``bool`` inside.

    Parameters
    ----------
    *inner_parsers: components.Parser[object]
        The parsers to use to parse the items inside the tuple. These define
        the inner types and the allowed number of items in the in the tuple.

        Defaults to a single string parser, i.e. a one-element tuple containing
        exactly one string.
    sep: str
        The separator to use. Can be any string, though a single character is
        recommended. Defaults to ",".

    """

    inner_parsers: typing.Tuple[parser_base.AnyParser, ...]
    sep: str

    def __init__(
        self,
        *inner_parsers: parser_base.AnyParser,
        sep: str = ",",
    ) -> None:
        self.inner_parsers = inner_parsers
        self.sep = sep

    async def loads(  # noqa: D102
        self, argument: str, *, source: disnake.Interaction
    ) -> _TupleT:
        # <<docstring inherited from parser_api.Parser>>
        parts = argument.split(self.sep)

        if len(parts) != len(self.inner_parsers):
            msg = f"Expected {len(self.inner_parsers)} arguments, got {len(parts)}."
            raise RuntimeError(msg)

        return typing.cast(
            _TupleT,
            tuple(
                [
                    await parser_base.try_loads(parser, part, source=source)
                    for parser, part in zip(self.inner_parsers, parts)
                ]
            ),
        )

    async def dumps(self, argument: _TupleT) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>
        if len(argument) != len(self.inner_parsers):
            msg = f"Expected {len(self.inner_parsers)} arguments, got {len(argument)}."
            raise RuntimeError(msg)

        return self.sep.join(
            [
                await aio.eval_maybe_coro(parser.dumps(part))
                for parser, part in zip(self.inner_parsers, argument)
            ]
        )


@parser_base.register_parser_for(typing.Collection)
class CollectionParser(parser_base.SourcedParser[_CollectionT]):
    """Parser type with support for collections of other types.

    This parser parses a string into a given container type and inner type, and
    vice versa.

    Note that this parser does not support tuples.

    Parameters
    ----------
    inner_parser: components.Parser[object]
        The parser to use to parse the items inside the collection. This defines
        the inner type for the collection. Sadly, due to typing restrictions,
        this is not enforced during type-checking. Defaults to a string parser.
    collection_type: Collection[object]
        The type of collection to use. This does not specify the inner type.
    sep: str
        The separator to use. Can be any string, though a single character is
        recommended. Defaults to ",".

    """

    inner_parser: parser_base.Parser[typing.Any]
    collection_type: typing.Type[_CollectionT]
    sep: str

    def __init__(
        self,
        inner_parser: typing.Optional[parser_base.Parser[typing.Any]] = None,
        *,
        collection_type: typing.Optional[typing.Type[_CollectionT]] = None,
        sep: str = ",",
    ) -> None:
        self.sep = sep
        self.collection_type = typing.cast(  # Pyright do be whack sometimes.
            typing.Type[_CollectionT],
            list if collection_type is None else _resolve_collection(collection_type),
        )
        self.inner_parser = (
            StringParser.default() if inner_parser is None else inner_parser
        )

    async def loads(  # noqa: D102
        self,
        argument: str,
        *,
        source: disnake.Interaction,
    ) -> _CollectionT:
        # <<docstring inherited from parser_api.Parser>>
        parsed = [
            await parser_base.try_loads(self.inner_parser, part, source=source)
            for part in argument.split(self.sep)
            if not part.isspace()  # TODO: Verify if this should be removed
        ]

        return self.collection_type(parsed)  # pyright: ignore[reportCallIssue]

    async def dumps(self, argument: _CollectionT) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>
        return ",".join(
            [
                await aio.eval_maybe_coro(  # Weird false flag in pyright...
                    self.inner_parser.dumps(part),  # pyright: ignore
                )
                for part in argument
            ]
        )


@parser_base.register_parser_for(typing.Union)  # pyright: ignore[reportArgumentType]
class UnionParser(parser_base.SourcedParser[_T], typing.Generic[_T]):
    """Parser type with support for unions.

    Provided parsers are sequentially tried until one passes. If none work, an
    exception is raised instead.

    Parameters
    ----------
    *inner_parsers: Optional[components.Parser[object]]
        The parsers with which to sequentially try to parse the argument.
        None can be provided as one of the parameters to make it optional.

    """

    inner_parsers: typing.Sequence[parser_base.Parser[typing.Any]]
    optional: bool

    def __init__(
        self, *inner_parsers: typing.Optional[parser_base.Parser[typing.Any]]
    ) -> None:
        if len(inner_parsers) < 2:
            msg = "A Union requires two or more type arguments."
            raise TypeError(msg)

        self.optional = False
        self.inner_parsers = []
        for parser in inner_parsers:
            if parser in _NONES:
                self.inner_parsers.append(NoneParser.default())
                self.optional = True

            else:
                self.inner_parsers.append(parser)

    async def loads(  # noqa: D102
        self, argument: str, *, source: disnake.Interaction
    ) -> _T:
        # <<docstring inherited from parser_api.Parser>>
        if not argument and self.optional:
            # Quick-return: if no argument was provided and the parser is
            # optional, just return None without trying any parsers.
            return typing.cast(_T, None)

        # Try all parsers sequentially. If any succeeds, return the result.
        for parser in self.inner_parsers:
            with contextlib.suppress(Exception):
                return await parser_base.try_loads(parser, argument, source=source)

        msg = "Failed to parse input to any type in the Union."
        raise RuntimeError(msg)

    async def dumps(self, argument: _T) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>
        if not argument and self.optional:
            return ""

        for parser in self.inner_parsers:
            if isinstance(argument, parser.default_types()):
                return await aio.eval_maybe_coro(parser.dumps(argument))

        msg = f"Failed to parse input {argument!r} to any type in the Union."
        raise RuntimeError(msg)
