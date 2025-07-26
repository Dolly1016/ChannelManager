from ast import Delete
import discord
from discord.ext import commands
from typing import Awaitable, Optional, Union, List, Callable, Protocol

class RecruitmentOwnerUICallbacks:

    def __init__(self, 
                 on_recruitment_owner: Callable[[discord.Interaction], Awaitable[tuple[bool, str]]]):
        self.on_recruitment_owner = on_recruitment_owner


class RecruitmentOwnerView(discord.ui.View):
    def __init__(self, callbacks: RecruitmentOwnerUICallbacks):
        super().__init__(timeout=None)
        self.callbacks = callbacks
        
    @discord.ui.button(label="募集主になる", style=discord.ButtonStyle.primary, emoji="💬")
    async def become_admin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self.callbacks.on_recruitment_owner(interaction)

        try:
            if result[0]:
                await interaction.response.defer(ephemeral=True)
            else:
                await interaction.response.send_message(result[1], ephemeral=True, delete_after=5)
        except Exception:
            pass



class RecruitmentOwnerUI:

    @staticmethod
    async def send_owner_selection_message(voice_channel: discord.VoiceChannel, callbacks: RecruitmentOwnerUICallbacks) -> Optional[discord.Message]:

        try:
            if voice_channel is None:
                print("Channel is None!")
                return None
            
            # Generate the embed message
            embed = discord.Embed(
                title="募集主がいません！",
                description="次に募集するユーザが下のボタンを押してください。",
                color=discord.Color.blue()
            )
            
            # Generate view for owner offer
            view = RecruitmentOwnerView(callbacks)
            
            # Send the message
            message = await voice_channel.send(embed=embed, view=view)
            return message
            
        except Exception as e:
            print(f"An error occurred while sending the message {e}")
            return None
