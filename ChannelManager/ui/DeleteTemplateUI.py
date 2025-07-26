import re
import discord
from typing import Awaitable, Optional, Union, List, Callable, Protocol
from ChannelSettings import ChannelSetting, ChannelLiveSetting
        

class DeleteTemplateView(discord.ui.View):
    def __init__(self, templates: dict[str,str], callback: Callable[[discord.Interaction], Awaitable[None]]):
        super().__init__(timeout=None)
        self.__add_templates_item(templates, callback)

    def __add_templates_item(self, templates: dict[str,str], callback: Callable[[discord.Interaction], Awaitable[None]]):
        def add_template_item(key: str, value: str):
            async def button_callback(interaction: discord.Interaction):
                templates.pop(key)
                await callback(interaction)
                try:
                    await interaction.message.delete()
                except Exception:
                    # If the message is already deleted, we can ignore the error
                    pass

            button = discord.ui.Button(label="削除: " + key, style=discord.ButtonStyle.red)
            button.callback = button_callback
            button.row = 0
            
            self.add_item(button)

        for key, value in templates.items():
            add_template_item(key, value)

class DeleteTemplateUI:
    @staticmethod
    async def send_edit_recruitment_message(interaction: discord.Interaction, template: dict[str,str], callback: Callable[[discord.Interaction], Awaitable[None]]) -> Optional[discord.Message]:
        try:
            view = DeleteTemplateView(template, callback)
            return await interaction.response.send_message(content="定型文の保存数が上限に達しています。\n削除する定型文を選択してください。", delete_after=20, view=view, ephemeral=True)
        except Exception as e:
            print(f"An error occurred while sending the message {e}")
            return None
