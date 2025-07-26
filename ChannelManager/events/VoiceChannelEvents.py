import discord
from discord.ext import commands
from GameVoiceChannelManager import GameVoiceChannelManager
import NicknameUtils

class VoiceChannelEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Ignore bot members
        if member.bot:
            return
        
        # If the voice channel has not changed, do nothing
        if before.channel == after.channel:
            return

        if before.channel is not None:
            await GameVoiceChannelManager().on_left_member(member, before.channel)

        if after.channel is not None:
            await GameVoiceChannelManager().on_join_member(member, after.channel)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if NicknameUtils.is_spectator(before) == NicknameUtils.is_spectator(after):
            return

        if after.voice == None or after.voice.channel == None:
            return
        
        vc = GameVoiceChannelManager().get_channel(after.voice.channel.id)

        if vc is not None:
            vc.on_update_member()

async def setup(bot):
    await bot.add_cog(VoiceChannelEvents(bot))