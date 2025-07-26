import re
import discord
from discord.ext import commands
from typing import Awaitable, Optional, Union, List, Callable, Protocol

from discord.ui import UserSelect
from ChannelSettings import ChannelLiveSetting, ChannelSetting
import NicknameUtils
from ui.RecruitmentUI import UserData
from ui.DeleteTemplateUI import DeleteTemplateUI

class ManagementUICallbacks:

    def __init__(self, 
                 on_change_to_player: Callable[[discord.Interaction], None],
                 on_change_to_spectator: Callable[[discord.Interaction], None],
                 on_edit_recruitment: Callable[[discord.Interaction], Awaitable[tuple[bool, str]]],
                 on_release_owner: Callable[[discord.Interaction], Awaitable[None]],
                 on_change_max_users: Callable[[discord.Interaction, int], Awaitable[None]]
                 ):
        self.on_change_to_player = on_change_to_player
        self.on_change_to_spectator = on_change_to_spectator
        self.on_edit_recruitment = on_edit_recruitment
        self.on_release_owner = on_release_owner
        self.on_change_max_users = on_change_max_users

class TemplateTextModal(discord.ui.Modal):
    def __init__(self, templates: dict[str,str], category: str, text: str):
        super().__init__(title="定型文の登録")

        self.add_item(
            discord.ui.TextInput(
                label="定型文の名前",
                placeholder="ここに入力...",
                style=discord.TextStyle.short,
                required=True, 
                max_length=4, 
            )
        )
        self.templates = templates
        self.category = category
        self.text = text

    async def on_submit(self, interaction: discord.Interaction) -> None:
        user_input = self.children[0].value
        self.templates[user_input] = self.text
        UserData().push_template(interaction.user, self.templates, self.category)
        await interaction.response.send_message("定型文を登録しました。", delete_after=5)
        
class NumberSelectView(discord.ui.View):
    def __init__(self, owner: discord.Member, callback: Callable[[discord.Interaction, int], None]):
        super().__init__(timeout=None)

        options = [discord.SelectOption(label=str(i + 1), value=str(i + 1)) for i in range(20)]
        select = discord.ui.Select(placeholder="最大人数を選んでください...", options=options)

        async def inner_callback(interaction: discord.Interaction):
            await callback(interaction, int(select.values[0]))
        select.callback = inner_callback

        self.add_item(select)

class ManagementView(discord.ui.View):

    def __init__(self, callbacks: ManagementUICallbacks, channel_settings: ChannelSetting, live_settings: ChannelLiveSetting, owner: discord.Member):
        super().__init__(timeout=None)
        self.callbacks = callbacks
        self.channel_settings = channel_settings
        self.live_settings = live_settings
        self.owner = owner

        if channel_settings.with_number_status and channel_settings.can_edit_max_number:
            async def number_callback(interaction: discord.Interaction):
                if await self.__can_use(interaction) and await self.__has_settings(interaction):
                    await interaction.response.send_message(content="募集人数を選択してください。", ephemeral=True, delete_after=20, view=NumberSelectView(self.owner, self.callbacks.on_change_max_users))

            button_number = discord.ui.Button(label="募集人数を変更", style=discord.ButtonStyle.gray, emoji="👥")
            button_number.callback = number_callback
            button_number.row = 2
            self.add_item(button_number)
       
    async def __can_use(self, interaction: discord.Interaction):
        if self.owner is None:
            await interaction.response.send_message("募集主が決定してから使用できます。", ephemeral=True, delete_after=5)
            return False
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message("募集主のみ使用できます。", ephemeral=True, delete_after=5)
            return False
        return True

    async def __has_settings(self, interaction: discord.Interaction):
        if self.live_settings is None:
            await interaction.response.send_message("募集文の投稿後に使用できます。", ephemeral=True, delete_after=5)
            return False
        return True

    @discord.ui.button(label="観戦する", style=discord.ButtonStyle.gray, emoji="👀", row = 0)
    async def change_to_spectator_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await NicknameUtils.change_to_spectator(interaction.user)
        await interaction.response.send_message(result[1], ephemeral=True, delete_after=5)
        if result[0]:
            await self.callbacks.on_change_to_spectator(interaction)

    @discord.ui.button(label="参加する", style=discord.ButtonStyle.green, emoji="🎮", row = 0)
    async def change_to_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await NicknameUtils.change_to_player(interaction.user)
        await interaction.response.send_message(result[1], ephemeral=True, delete_after=5)
        if result[0]:
            await self.callbacks.on_change_to_player(interaction)

    @discord.ui.button(label="募集文を編集", style=discord.ButtonStyle.grey, emoji="📝", row = 1)
    async def edit_recruitment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.__can_use(interaction):
            result = await self.callbacks.on_edit_recruitment(interaction)
            if result[0]:
                await interaction.response.defer(ephemeral=True) 
            else:
                await interaction.response.send_message(result[1], 5)

    @discord.ui.button(label="定型文に保存", style=discord.ButtonStyle.grey, emoji="💿", row = 1)
    async def save_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.__can_use(interaction) and await self.__has_settings(interaction):
            templates = UserData().get_user_texts(interaction.user, self.channel_settings.category).templates

            async def send_modal(interaction: discord.Interaction):
                await interaction.response.send_modal(TemplateTextModal(templates, self.channel_settings.category, self.live_settings.message))

            if len(templates) >= UserData.max_templates:
                await DeleteTemplateUI.send_edit_recruitment_message(interaction, templates, send_modal)
            else:
                await send_modal(interaction)

    @discord.ui.button(label="募集主を譲渡する", style=discord.ButtonStyle.red, emoji="✖", row = 1)
    async def release_owner(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.__can_use(interaction):
            await self.callbacks.on_release_owner(interaction)
            await interaction.response.defer(ephemeral=True)
            

class ManagementUI:

    @staticmethod
    async def send_management_message(voice_channel: discord.VoiceChannel, channel_settings: ChannelSetting, live_settings: Optional[ChannelLiveSetting], owner: discord.Member, callbacks: ManagementUICallbacks) -> Optional[discord.Message]:
        try:
            if voice_channel is None:
                print("Channel is None!")
                return None
            
            # Generate the embed message
            embed = discord.Embed(
                title="VC管理",
                description="部屋主: " + owner.display_name,
                color=discord.Color.blue()
            )
            
            # Generate view for owner offer
            view = ManagementView(callbacks, channel_settings, live_settings, owner)
            
            # Send the message
            message = await voice_channel.send(embed=embed, view=view)
            return message
            
        except Exception as e:
            print(f"An error occurred while sending the message {e}")
            return None
