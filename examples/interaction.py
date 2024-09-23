"""A simple example on the use of interaction wrappers."""

import os
import typing

import disnake
from disnake.ext import commands, components

bot = commands.InteractionBot()

manager = components.get_manager()
manager.add_to_bot(bot)


@manager.register
class MyButton(components.RichButton):
    label: typing.Optional[str] = "\N{PROHIBITED SIGN} 클릭"
    style: disnake.ButtonStyle = disnake.ButtonStyle.red

    async def callback(self, interaction: components.MessageInteraction) -> None:
        await interaction.response.send_message("Don't touch me!")


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
@components.wrap_interaction_for
async def with_wrapped_callback(interaction: components.CommandInteraction):
    print(MyButton().label)

    return await interaction.response.send_message(components=MyButton())


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def with_manual_wrap(interaction: disnake.CommandInteraction):
    wrapped = components.wrap_interaction(interaction)
    return await wrapped.response.send_message(components=MyButton())


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def without_wrap(interaction: disnake.CommandInteraction):
    return await interaction.response.send_message(
        components=await MyButton().as_ui_component()
    )


bot.run(os.getenv("EXAMPLE_TOKEN"))
