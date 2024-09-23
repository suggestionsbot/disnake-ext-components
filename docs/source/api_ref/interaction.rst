.. currentmodule:: disnake.ext.components

Interaction Implementation
==========================

.. automodule:: components.interaction

Functions
---------

.. autofunction:: components.interaction.wrap_interaction

.. autofunction:: components.interaction.wrap_interaction_for

Classes
-------

.. note::
    These classes are all wrapper classes that allow sending *disnake-ext-components*' :class:`~components.api.component.RichComponent`\s without having to manually call :meth:`~components.api.component.RichComponent.as_ui_component` on them.
    Besides this, these classes are functionally equivalent to their disnake counterparts.

.. autoclass:: components.interaction.WrappedInteraction

    .. seealso::
        This class is a wrapper of :class:`disnake.Interaction`;
        everything on it is available to this class.

.. autoclass:: components.interaction.MessageInteraction

    .. seealso::
        This class is a wrapper of :class:`disnake.MessageInteraction`;
        everything on it is available to this class.

.. autoclass:: components.interaction.CommandInteraction

    .. seealso::
        This class is a wrapper of :class:`disnake.ApplicationCommandInteraction`;
        everything on it is available to this class.
