from typing import Callable

import discord


class ConfirmationDialog(discord.ui.View):
    def __init__(self, confirm_message: str = "Confirming...", cancel_message: str = "Cancelling...",
                 confirm_callback: Callable = None, cancel_callback: Callable = None, timeout_message: str = None):
        super().__init__()
        self.value = None

        self.confirm_message = confirm_message
        self.cancel_message = cancel_message
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        self.timeout_message = timeout_message

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', emoji='✅', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=self.confirm_message, view=None)
        self.value = True
        self.stop()
        if self.confirm_callback is not None:
            # todo: maybe defer
            await self.confirm_callback(interaction)

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', emoji='❎', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=self.cancel_message, view=None)
        self.value = False
        self.stop()
        if self.cancel_callback is not None:
            # todo: maybe defer
            await self.cancel_callback(interaction)

    async def on_timeout(self) -> None:
        # todo: inform of timeout
        # await ctx.send("I'll take this as a no...")
        pass
