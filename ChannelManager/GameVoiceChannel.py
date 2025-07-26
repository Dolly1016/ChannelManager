import re
from tkinter import SEL
from typing import Optional, Protocol, Tuple
from discord import Message, VoiceChannel, Member
from discord.abc import GuildChannel
import discord
import NicknameUtils
from ChannelSettings import ChannelSetting, ChannelLiveSetting
from ui.RecruitmentOwnerUI import RecruitmentOwnerUI, RecruitmentOwnerUICallbacks
from ui.ManagementUI import ManagementUI, ManagementUICallbacks
from ui.RecruitmentUI import RecruitmentUI, RecruimentUICallbacks


class GameVoiceChannel:
    """
    The class representing a game voice channel.
    """
    
    def __init__(self, voice_channel: VoiceChannel | GuildChannel, setting: ChannelSetting):
        """
        The constructor for GameVoiceChannel class.
        
        Parameters:
            voice_channel (discord.VoiceChannel): the voice channel object
            owner_id (int, optional): owner ID of the voice channel (default is None)
            no_owner_ui_message (discord.Message, optional): message for the UI when there is no owner (default is None)
            management_ui_message (discord.Message, optional): message for the management UI (default is None)
        """
        self.voice_channel = voice_channel
        self.vc_id = voice_channel.id
        self.owner: Optional[Member] = None
        self.no_owner_ui_message: Optional[Message] = None
        self.management_ui_message: Optional[Message] = None
        self.recruitment_ui_message: Optional[Message] = None
        self.recruitment_message: Optional[Message] = None
        self.setting = setting
        self.current_setting: Optional[ChannelLiveSetting] = None

    # Recruitment Message

    async def __send_recruitment_message(self) -> Tuple[bool, str]:
        if self.setting.recruitment_channel is None:
            return [False, "このチャンネルでの募集は無効です。"]

        try:
            send_to = await self.voice_channel.guild.fetch_channel(self.setting.recruitment_channel)
        except Exception as e:
            print(f"There is no a recruitment channel! unknown channel id: {self.setting.recruitment_channel} \ne: {e}")
            return [False, "募集チャンネルを見つけられませんでした。"]
        
        try:
            self.recruitment_message = await send_to.send(embed=self.__get_recuitment_embed())
        except Exception as e:
            print(f"An error occurred while sending a recruitment message. {e}")
            return [False, "募集の掲示中にエラーが発生しました。"]

        return [True, "募集を投稿しました。"]

    async def __update_recruitment_message(self) -> Tuple[bool, str]:
        if self.owner is None:
            return [False, "募集が開始されていません。"]

        if self.recruitment_message is None:
            return [False, "募集が開始されていません。"]
        
        try:
            await self.recruitment_message.edit(embed=self.__get_recuitment_embed())
        except Exception as e:
            print(f"An error occurred while updating the recruitment message: {e}")
            return [False, "募集の掲示中にエラーが発生しました。"]

        return [True, "募集を更新しました。"]
    
    async def __update_vc_status(self):
        await self.voice_channel.edit(status=self.__get_left_players_text())

    async def update_status(self):
        await self.__update_recruitment_message()
        await self.__update_vc_status()

    def __get_recuitment_embed(self):
        embed = discord.Embed(title=self.voice_channel.name, color=discord.Color.red(), description=self.current_setting.message)

        embed.add_field(name="募集主", value=self.owner.display_name, inline=True)
        if self.setting.with_number_status:
            embed.add_field(name="募集人数", value=self.__get_left_players_text(), inline=True)
        if self.setting.with_live_status:
            embed.add_field(name="他ゲームの配信", value=self.current_setting.live_status, inline=True)
        if self.setting.with_random_status:
            embed.add_field(name="ゲーム中の雑談", value=self.current_setting.random_status, inline=True)

        return embed

    def __get_left_players_text(self):
        left = self.get_max_players() - self.count_players()
        return "@" + str(left) if left > 0 else "〆"

    # NoOwnerUI

    async def __delete_no_owner_ui(self):
        """
        Delete the no owner UI message if it exists.
        """
        if self.no_owner_ui_message is None:
            return
        try:
            await self.no_owner_ui_message.delete()
        except Exception as e:
            print(f"An error occurred while deleting the message: {e}")
        finally:
            self.no_owner_ui_message = None

    async def __show_no_owner_ui(self):
        """
        Show the no owner UI message in the voice channel.
        If the message already exists, it will be deleted first.
        """
        if self.no_owner_ui_message is not None:
            await self.__delete_no_owner_ui()

        async def callback(interaction : discord.Interaction) -> tuple[bool, str]:
            return await self.try_set_owner(interaction.user, interaction.message)
        self.no_owner_ui_message = await RecruitmentOwnerUI.send_owner_selection_message(self.voice_channel, RecruitmentOwnerUICallbacks(callback))

    # ManagementUI

    async def __delete_management_ui(self):
        """
        Delete the management UI message if it exists.
        """
        if self.management_ui_message is None:
            return
        try:
            await self.management_ui_message.delete()
        except Exception as e:
            print(f"An error occurred while deleting the message: {e}")
        finally:
            self.management_ui_message = None

    async def __show_management_ui(self):
        """
        Show the management UI message in the voice channel.
        """
        if self.management_ui_message is not None:
            await self.__delete_management_ui()

        async def change_players_callback(interaction : discord.Interaction):
            await self.update_status()

        member = self.owner
        if NicknameUtils.is_spectator(member):
            await NicknameUtils.change_to_player(member)
        self.no_owner_ui_message = await ManagementUI.send_management_message(self.voice_channel, member, ManagementUICallbacks(change_players_callback, change_players_callback))

    # RecruimentUI

    async def __delete_recruitment_ui(self):
        """
        Delete the recruiment UI message if it exists.
        """
        if self.recruitment_ui_message is None:
            return
        try:
            await self.recruitment_ui_message.delete()
        except Exception as e:
            print(f"An error occurred while deleting the message: {e}")
        finally:
            self.recruitment_ui_message = None

    async def __show_recruitment_ui(self):
        """
        Show the recruiment UI message in the voice channel.
        """
        if self.recruitment_ui_message is not None:
            await self.__delete_recruitment_ui()

        async def start_recruitment_callback(interaction : discord.Interaction, live_settings: ChannelLiveSetting):
            self.current_setting = live_settings
            result = await self.__send_recruitment_message()
            await interaction.response.send_message(result[1], ephemeral=True, delete_after=5)
            if result[0]:
                await interaction.message.delete()

        self.recruitment_ui_message = await RecruitmentUI.send_edit_recruitment_message(self.voice_channel, self.setting, self.owner, RecruimentUICallbacks(start_recruitment_callback))

    def count_players(self):
        players = 0
        for member in self.voice_channel.members:
           if not NicknameUtils.is_spectator(member):
               players += 1
        return players

    def get_max_players(self):
        #TODO: チャンネルごとの個別の最大人数に対応
        return self.setting.max_number

    async def try_set_owner(self, owner: Member, message: Message) -> tuple[bool, str]:
        """
        Try to set the owner of the voice channel.
        
        Parameters:
            owner_id (int): ID of the new owner
            message (discord.Message): message that sent this request
        Returns:
            tuple[bool, str]: a tuple containing a boolean indicating success or failure, and a message string
        """

        if self.owner is not None:
            if self.owner.id == owner.id:
                return [False, "既にあなたが募集主です。"]
            return [False, "既に募集主が決定しています。"]

        if self.no_owner_ui_message is None:
            return [False, "現在は募集主変更のリクエストを受け付けていません。"]

        if self.no_owner_ui_message.id != message.id:
            return [False, "無効なインタラクションです。"]

        if self.owner is None:
            await self.set_owner(owner)
            return [True, "募集主のリクエストを受理しました。"]
        return False

    async def set_owner(self, owner: Optional[Member]) -> None:
        """
        Set the owner of the voice channel.
        
        Parameters:
            owner_id (int, optional): ID of the new owner
        """
        self.owner = owner
        if owner is None:
            await self.__show_no_owner_ui()
            await self.__delete_management_ui()
            await self.__delete_recruitment_ui()
        else:
            await self.__delete_no_owner_ui()
            await self.__show_management_ui()
            await self.__show_recruitment_ui()

    async def on_left_member(self, member: Member) -> None:
        """
        Handle the event when a member leaves the voice channel.
        
        Parameters:
            member (discord.Member): the member who left the voice channel
        """
        if self.owner is not None and self.owner.id == member.id:
            await self.set_owner(None)

        await self.update_status()

    async def on_join_member(self, member: Member) -> None:
        """
        Handle the event when a member joins the voice channel.
        
        Parameters:
            member (discord.Member): the member who joined the voice channel
        """
        if self.owner is None:
            if len(self.voice_channel.members) == 1:
                await self.set_owner(member)
            else:
                await self.__show_no_owner_ui()

        if self.count_players() <= self.get_max_players():
            await NicknameUtils.change_to_player(member)
        else:
            await NicknameUtils.change_to_spectator(member)

        await self.update_status()

    async def on_update_member(self) -> None:
        await self.update_status()



        