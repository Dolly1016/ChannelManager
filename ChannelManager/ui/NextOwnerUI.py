import re
import discord
from discord.ext import commands
from typing import Awaitable, Optional, Union, List, Callable, Protocol

from discord.ui import UserSelect
from ChannelSettings import ChannelLiveSetting, ChannelSetting

class UserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180) # �^�C���A�E�g��݂���i3���j

    # discord.ui.UserSelect ���f�R���[�^�Œǉ�
    @discord.ui.select(
        cls=discord.ui.UserSelect, # ���ꂪ���[�U�[�I���Z���N�^�[�ł��邱�Ƃ�����
        placeholder="���[�U�[��I�����Ă�������...",
        min_values=1,
        max_values=1, 
        
    )
    async def select_user_callback(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        # ���[�U�[���I�����ꂽ�Ƃ��ɂ��̃R�[���o�b�N�����s�����
        # select.values �ɂ͑I�����ꂽ���[�U�[�̃��X�g���܂܂��
        selected_user = select.values[0] # max_values=1 �Ȃ̂ŁA�ŏ��̗v�f���擾

        await interaction.response.send_message(
            f'�I�����ꂽ���[�U�[: {selected_user.mention} (ID: `{selected_user.id}`)',
            ephemeral=True # ���̃��[�U�[�ɂ͌����Ȃ�
        )

    async def on_timeout(self):
        # �^�C���A�E�g�����ꍇ�̏���
        # self.message ������΁A���̃��b�Z�[�W��ҏW���Ė����ɂ���Ȃ�
        if self.message:
            await self.message.edit(content="�Z���N�^�[���^�C���A�E�g���܂����B", view=None)

