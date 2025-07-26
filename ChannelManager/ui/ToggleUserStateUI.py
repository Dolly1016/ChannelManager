import discord
from typing import Awaitable, Optional, Union, List, Callable, Protocol
import NicknameUtils

class ToggleUserStateView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
       
    @discord.ui.button(label="観戦する", style=discord.ButtonStyle.gray, emoji="👀", row = 0)
    async def change_to_spectator_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await NicknameUtils.change_to_spectator(interaction.user)
        await interaction.response.send_message(result[1], ephemeral=True, delete_after=5)

    @discord.ui.button(label="参加する", style=discord.ButtonStyle.green, emoji="🎮", row = 0)
    async def change_to_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await NicknameUtils.change_to_player(interaction.user)
        await interaction.response.send_message(result[1], ephemeral=True, delete_after=5)

            

class ToggleUserStateUI:

    @staticmethod
    async def send_toggle_state_message(voice_channel: discord.VoiceChannel) -> Optional[discord.Message]:
        try:
            if voice_channel is None:
                print("Channel is None!")
                return None
            
            # Generate the embed message
            embed = discord.Embed(
                title="VC管理",
                description="観戦状態を切り替えられます。",
                color=discord.Color.blue()
            )
            
            # Generate view
            view = ToggleUserStateView()
            
            # Send the message
            message = await voice_channel.send(embed=embed, view=view)
            return message
            
        except Exception as e:
            print(f"An error occurred while sending the message {e}")
            return None
