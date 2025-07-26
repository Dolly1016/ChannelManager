import re
import discord
from discord.ext import commands
from typing import Awaitable, Optional, Union, List, Callable, Protocol
import NicknameUtils

class ManagementUICallbacks:

    def __init__(self, 
                 on_change_to_player: Callable[[discord.Interaction], None],
                 on_change_to_spectator: Callable[[discord.Interaction], None],
                 # on_change_to_player: Callable[[discord.Interaction], Awaitable[tuple[bool, str]]],
                 ):
        self.on_change_to_player = on_change_to_player
        self.on_change_to_spectator = on_change_to_spectator


class ManagementView(discord.ui.View):

    def __init__(self, callbacks: ManagementUICallbacks):
        super().__init__(timeout=None)
        self.callbacks = callbacks
        
    @discord.ui.button(label="観戦する", style=discord.ButtonStyle.gray, emoji="👀")
    async def change_to_spectator_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await NicknameUtils.change_to_spectator(interaction.user)
        await interaction.response.send_message(result[1], ephemeral=True, delete_after=5)
        if result[0]:
            await self.callbacks.on_change_to_spectator(interaction)

    @discord.ui.button(label="参加する", style=discord.ButtonStyle.green, emoji="🎮")
    async def change_to_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await NicknameUtils.change_to_player(interaction.user)
        await interaction.response.send_message(result[1], ephemeral=True, delete_after=5)
        if result[0]:
            await self.callbacks.on_change_to_player(interaction)

class ManagementUI:

    @staticmethod
    async def send_management_message(voice_channel: discord.VoiceChannel, owner: discord.Member, callbacks: ManagementUICallbacks) -> Optional[discord.Message]:
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
            view = ManagementView(callbacks)
            
            # Send the message
            message = await voice_channel.send(embed=embed, view=view)
            return message
            
        except Exception as e:
            print(f"An error occurred while sending the message {e}")
            return None
