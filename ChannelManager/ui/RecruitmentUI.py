import re
import discord
from discord.ext import commands
from typing import Awaitable, Optional, Union, List, Callable, Protocol
from ChannelSettings import ChannelSetting, ChannelLiveSetting, ChannelSettings, SelectsSetting
import NicknameUtils
from database.UserData import UserData

class RecruimentUICallbacks:
    def __init__(self, 
                 on_start_recruiment: Callable[[discord.Interaction, ChannelLiveSetting], None],
                 ):
        self.on_start_recruiment = on_start_recruiment

class RecruimentTextModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, on_determine_text:  Callable[[str], Awaitable[None]]):
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

    async def on_submit(self, interaction: discord.Interaction) -> None:
        user_input = self.children[0].value
        await self.on_determine_text(user_input)
        await interaction.response.defer(ephemeral=True)
        
class CustomSelectsView(discord.ui.View):
    def __init__(self, selects_setting: SelectsSetting, callback: Callable[[discord.Interaction, str], None]):
        super().__init__(timeout=None)

        options = [discord.SelectOption(label=s, value=s) for s in selects_setting.selects]
        if selects_setting.default_value is None:
            options.insert(0, discord.SelectOption(label="(選択無し)", value="#EMPTY"))
        select = discord.ui.Select(placeholder="選択してください...", options=options)

        async def inner_callback(interaction: discord.Interaction):
            await callback(interaction, select.values[0] if select.values[0] != "#EMPTY" else None)
        select.callback = inner_callback

        self.add_item(select)


class RecruimentView(discord.ui.View):
    def __init__(self, callbacks: RecruimentUICallbacks, embed_updater: Callable[[str], Awaitable[None]], owner: discord.Member, channel_settings: ChannelSetting, live_settings: Optional[ChannelLiveSetting]):
        super().__init__(timeout=None)
        self.user_texts = UserData().get_user_texts(owner, channel_settings.category)
        self.callbacks = callbacks
        self.owner = owner
        self.text = (live_settings is not None and live_settings.message) or self.user_texts.last_text_recruitment or "誰でもどうぞ！"
        self.live_status = (live_settings is not None and live_settings.live_status) or self.user_texts.last_text_live or "可"
        self.random_status = (live_settings is not None and live_settings.random_status) or self.user_texts.last_text_random or "可"
        self.embed_updater = embed_updater
        self.channel_settings = channel_settings
        self.last_max_number = (live_settings is not None and live_settings.max_number) or None
        self.unused_row = 1
        self.selects: dict[str,str] = (live_settings is not None and live_settings.selects) or {}

        if len(self.user_texts.templates) > 0:
            self.__add_templates_item()

        if self.channel_settings.with_live_status:
            self.__add_live_status_item()
        if self.channel_settings.with_random_status:
            self.__add_random_status_item()

        self.__add_custom_selects_item()

        self.__add_post_item()

        
    async def __can_edit(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message("募集主のみ編集できます。", ephemeral=True, delete_after=5)
            return False
        return True

    @discord.ui.button(label="募集文を編集", style=discord.ButtonStyle.gray, emoji="📝",row=0)
    async def edit_text(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.__can_edit(interaction):
            await interaction.response.send_modal(RecruimentTextModal("募集文を編集", "募集文", self.__update_text))

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
        embed.add_field(name="募集文", value=self.text, inline=False)
        if self.channel_settings.with_live_status:
            embed.add_field(name="他ゲームの配信可否", value=self.live_status, inline=False)
        if self.channel_settings.with_random_status:
            embed.add_field(name="ゲーム中の雑談可否", value=self.random_status, inline=False)

        # Show custom selections
        for selects_id in self.channel_settings.selects:
            selects_setting: Optional[SelectsSetting] = ChannelSettings().get_selects_setting(selects_id)
            if selects_id is None:
                continue
            select = (self.selects[selects_id] if selects_id in self.selects else None) or selects_setting.default_value or "(未設定)"
            embed.add_field(name=selects_setting.label, value=select, inline=False)
        return embed;

    def __add_post_item(self):
        async def post_callback(interaction: discord.Interaction):
            live_setting = ChannelLiveSetting(self.live_status, self.random_status, self.last_max_number, self.text, self.selects)
            UserData().push_history(self.owner, live_setting, self.channel_settings)
            await self.callbacks.on_start_recruiment(interaction, live_setting)

        button = discord.ui.Button(label="投稿", style=discord.ButtonStyle.green)
        button.callback = post_callback
        button.row = self.unused_row
        self.add_item(button)
        self.unused_row += 1

    def __add_live_status_item(self):
        async def button_callback(interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                await interaction.response.send_modal(RecruimentTextModal("他ゲームの配信可否を編集", "他ゲームの配信可否", self.__update_live_text))

        async def binary_callback(allowed: bool, interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                await self.__update_live_text("可" if allowed else "不可")
                await interaction.response.defer(ephemeral=True)
                
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

        button_denied = discord.ui.Button(label="配信を禁止", style=discord.ButtonStyle.red)
        button_denied.callback = deny_callback
        button_denied.row = self.unused_row
        self.add_item(button_denied)

        self.unused_row += 1
        
    def __add_random_status_item(self):
        async def button_callback(interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                await interaction.response.send_modal(RecruimentTextModal("ゲーム中の雑談可否を編集", "ゲーム中の雑談可否", self.__update_random_text))

        async def binary_callback(allowed: bool, interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                await self.__update_random_text("可" if allowed else "不可")
                await interaction.response.defer(ephemeral=True)
                
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

        button_denied = discord.ui.Button(label="雑談を禁止", style=discord.ButtonStyle.red)
        button_denied.callback = deny_callback
        button_denied.row = self.unused_row
        self.add_item(button_denied)

        self.unused_row += 1

    def __add_custom_selects_item(self):
        valid_selects: list[tuple[str, SelectsSetting]] = []
        for selects_id in self.channel_settings.selects:
            selects = ChannelSettings().get_selects_setting(selects_id)
            if selects is not None:
                valid_selects.append([selects_id, selects])

        if len(valid_selects) == 0:
            return

        options = [discord.SelectOption(label=entry[1].label + " を編集", value=entry[0]) for entry in valid_selects]
        select_ui = discord.ui.Select(placeholder="編集する項目を選んでください...", options=options)
        select_ui.row = self.unused_row

        

        async def inner_callback(interaction: discord.Interaction):
            if await self.__can_edit(interaction):
                current_select_id = select_ui.values[0]
                async def selector_callback(interaction: discord.Interaction, selects: str):
                    await interaction.response.defer(ephemeral=True)
                    self.selects[current_select_id] = selects
                    await self.__update_embed()
                await interaction.response.send_message(content="テキストを選択してください。", ephemeral=True, delete_after=20, view=CustomSelectsView(ChannelSettings().get_selects_setting(current_select_id), selector_callback))
        select_ui.callback = inner_callback
        self.add_item(select_ui)

        self.unused_row += 1


        

    def __add_templates_item(self):
        def add_template_item(key: str, value: str):
            async def button_callback(interaction: discord.Interaction):
                if await self.__can_edit(interaction):
                    await self.__update_text(value)
                    await interaction.response.defer(ephemeral=True)

            button = discord.ui.Button(label="定型文: " + key, style=discord.ButtonStyle.grey)
            button.callback = button_callback
            button.row = 0
            

            self.add_item(button)

        for key, value in self.user_texts.templates.items():
            add_template_item(key, value)

class RecruitmentUI:
    
    @staticmethod
    async def send_edit_recruitment_message(voice_channel: discord.VoiceChannel, setting: ChannelSetting, live_setting: Optional[ChannelLiveSetting], owner: discord.Member, callbacks: RecruimentUICallbacks) -> Optional[discord.Message]:
        try:
            if voice_channel is None:
                print("Channel is None!")
                return None
            
            # Generate the embed message
            message: discord.Message = None
            async def update_message(embed: discord.Embed):
                await message.edit(embed=embed)
            
            view = RecruimentView(callbacks, update_message, owner, setting, live_setting)
            
            # Send the message
            message = await voice_channel.send(embed=view.get_embed(), view=view)
            
            return message
            
        except Exception as e:
            print(f"An error occurred while sending the message {e}")
            return None
