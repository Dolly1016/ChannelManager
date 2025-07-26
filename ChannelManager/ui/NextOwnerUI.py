import re
import discord
from discord.ext import commands
from typing import Awaitable, Optional, Union, List, Callable, Protocol

from discord.ui import UserSelect
from ChannelSettings import ChannelLiveSetting, ChannelSetting

class UserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180) # タイムアウトを設ける（3分）

    # discord.ui.UserSelect をデコレータで追加
    @discord.ui.select(
        cls=discord.ui.UserSelect, # これがユーザー選択セレクターであることを示す
        placeholder="ユーザーを選択してください...",
        min_values=1,
        max_values=1, 
        
    )
    async def select_user_callback(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        # ユーザーが選択されたときにこのコールバックが実行される
        # select.values には選択されたユーザーのリストが含まれる
        selected_user = select.values[0] # max_values=1 なので、最初の要素を取得

        await interaction.response.send_message(
            f'選択されたユーザー: {selected_user.mention} (ID: `{selected_user.id}`)',
            ephemeral=True # 他のユーザーには見せない
        )

    async def on_timeout(self):
        # タイムアウトした場合の処理
        # self.message があれば、そのメッセージを編集して無効にするなど
        if self.message:
            await self.message.edit(content="セレクターがタイムアウトしました。", view=None)

