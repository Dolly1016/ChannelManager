import re
import discord
from discord.ext import commands
from typing import Awaitable, Optional, Union, List, Callable, Protocol
from ChannelSettings import ChannelSetting, ChannelLiveSetting
import NicknameUtils


class RecruimentUICallbacks:
    def __init__(self, 
                 on_start_recruiment: Callable[[discord.Interaction, ChannelLiveSetting], None],
                 ):
        self.on_start_recruiment = on_start_recruiment

class RecruimentTextModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, complete_message: str, on_determine_text:  Callable[[str], Awaitable[None]]):
        super().__init__(title=title)

        self.add_item(
            discord.ui.TextInput(
                label=label,
                placeholder="ここに入力...",
                style=discord.TextStyle.short,
                required=True, 
                max_length=100, 
            )
        )
        self.on_determine_text = on_determine_text
        self.complete_message = complete_message

    async def on_submit(self, interaction: discord.Interaction) -> None:
        user_input = self.children[0].value
        await self.on_determine_text(user_input)
        await interaction.response.send_message(self.complete_message, delete_after=5)
        

class RecruimentView(discord.ui.View):
    def __init__(self, callbacks: RecruimentUICallbacks, embed_updater: Callable[[str], Awaitable[None]], owner: discord.Member, with_live_status: bool, with_random_status: bool):
        super().__init__(timeout=None)
        self.callbacks = callbacks
        self.owner = owner
        self.text = "誰でもどうぞ！"
        self.live_status = "可"
        self.random_status = "可"
        self.embed_updater = embed_updater
        self.with_live_status = with_live_status
        self.with_random_status = with_random_status

        self.unused_row = 1
        if with_live_status:
            self.__add_live_status_item()
        if with_random_status:
            self.__add_random_status_item()

        self.__add_post_item()

        
    async def __can_edit(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message("募集主のみ編集できます。", ephemeral=True, delete_after=5)
            return False
        return True

    @discord.ui.button(label="募集文を編集", style=discord.ButtonStyle.gray, emoji="📝",row=0)
    async def edit_text(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.__can_edit(interaction):
            await interaction.response.send_modal(RecruimentTextModal("募集文を編集", "募集文", "募集文を更新しました。", self.__update_text))

    async def __update_embed(self):
        await self.embed_updater(self.get_embed())

    async def __update_text(self, text: str):
        self.text = text
        await self.__update_embed()

    async def __update_live_text(self, text: str):
        self.live_status = text
        await self.__update_embed()

    async def __update_random_text(self, text: str):
        self.random_status = text
        await self.__update_embed()

    def get_embed(self):
        embed = discord.Embed(title="募集文投稿", description="募集を投稿してください。", color=discord.Color.blue())
        embed.add_field(name="部屋主", value=self.owner.display_name)
        embed.add_field(name="募集文", value=self.text)
        if self.with_live_status:
            embed.add_field(name="他ゲームの配信可否", value=self.live_status)
        if self.with_random_status:
            embed.add_field(name="ゲーム中の雑談可否", value=self.random_status)
        return embed;

    def __add_post_item(self):
        async def post_callback(interaction: discord.Interaction):
            await self.callbacks.on_start_recruiment(interaction, ChannelLiveSetting(self.live_status, self.random_status, None, self.text))

        button = discord.ui.Button(label="投稿", style=discord.ButtonStyle.green)
        button.callback = post_callback
        button.row = self.unused_row
        self.add_item(button)
        self.unused_row += 1

    def __add_live_status_item(self):
        async def button_callback(interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                await interaction.response.send_modal(RecruimentTextModal("他ゲームの配信可否を編集", "他ゲームの配信可否", "他ゲームの配信可否を更新しました。", self.__update_live_text))

        async def binary_callback(allowed: bool, interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                await self.__update_live_text("可" if allowed else "不可")
                await interaction.response.send_message("他ゲームの配信可否を更新しました。", delete_after=5)
                
        async def allow_callback(interaction: discord.Interaction):
            await binary_callback(True, interaction)
        async def deny_callback(interaction: discord.Interaction):
            await binary_callback(False, interaction)

        button = discord.ui.Button(label="カスタム配信設定",emoji="🎥", style=discord.ButtonStyle.grey)
        button.callback = button_callback
        button.row = self.unused_row
        self.add_item(button)

        button_allowed = discord.ui.Button(label="配信を許可", style=discord.ButtonStyle.green)
        button_allowed.callback = allow_callback
        button_allowed.row = self.unused_row
        self.add_item(button_allowed)

        button_denied = discord.ui.Button(label="配信を拒否", style=discord.ButtonStyle.red)
        button_denied.callback = deny_callback
        button_denied.row = self.unused_row
        self.add_item(button_denied)

        self.unused_row += 1
        
    def __add_random_status_item(self):
        async def button_callback(interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                await interaction.response.send_modal(RecruimentTextModal("ゲーム中の雑談可否を編集", "ゲーム中の雑談可否", "ゲーム中の雑談可否を更新しました。", self.__update_random_text))

        async def binary_callback(allowed: bool, interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                await self.__update_random_text("可" if allowed else "不可")
                await interaction.response.send_message("ゲーム中の雑談可否を更新しました。", delete_after=5)
                
        async def allow_callback(interaction: discord.Interaction):
            await binary_callback(True, interaction)
        async def deny_callback(interaction: discord.Interaction):
            await binary_callback(False, interaction)

        button = discord.ui.Button(label="カスタム雑談設定", emoji="💬", style=discord.ButtonStyle.grey)
        button.callback = button_callback
        button.row = self.unused_row
        self.add_item(button)

        button_allowed = discord.ui.Button(label="雑談を許可", style=discord.ButtonStyle.green)
        button_allowed.callback = allow_callback
        button_allowed.row = self.unused_row
        self.add_item(button_allowed)

        button_denied = discord.ui.Button(label="雑談を拒否", style=discord.ButtonStyle.red)
        button_denied.callback = deny_callback
        button_denied.row = self.unused_row
        self.add_item(button_denied)

        self.unused_row += 1

class RecruitmentUI:
    
    @staticmethod
    async def send_edit_recruitment_message(voice_channel: discord.VoiceChannel, setting: ChannelSetting, owner: discord.Member, callbacks: RecruimentUICallbacks) -> Optional[discord.Message]:
        try:
            if voice_channel is None:
                print("Channel is None!")
                return None
            
            # Generate the embed message
            message: discord.Message = None
            async def update_message(embed: discord.Embed):
                await message.edit(embed=embed)
            
            view = RecruimentView(callbacks, update_message, owner, setting.with_live_status, setting.with_random_status)
            
            # Send the message
            message = await voice_channel.send(embed=view.get_embed(), view=view)
            
            return message
            
        except Exception as e:
            print(f"An error occurred while sending the message {e}")
            return None
