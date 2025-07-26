import discord
from GameVoiceChannel import GameVoiceChannel
from ChannelSettings import ChannelSetting, ChannelSettings

class GameVoiceChannelManager:
    """
    The class representing a singleton manager for game voice channels.
    """

    _instance = None
    
    # getter for the singleton instance
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameVoiceChannelManager, cls).__new__(cls)
            cls._instance._channels = {}  # VoiceChannelのIDをキーとするマップ
        return cls._instance
    
    def __add_channel(self, game_voice_channel: GameVoiceChannel):
        """
        Add a GameVoiceChannel to the manager.
        """
        self._channels[game_voice_channel.vc_id] = game_voice_channel
        return game_voice_channel
        
    def __get_channel(self, channel_id):
        """
        Get a GameVoiceChannel by its ID.
        """
        return self._channels.get(channel_id)
    
    def __remove_channel(self, game_voice_channel: GameVoiceChannel):
        """
        Remove a GameVoiceChannel from the manager.
        """
        if game_voice_channel.vc_id in self._channels:
            del self._channels[game_voice_channel.vc_id]
            return True
        return False

    async def on_left_member(self, member: discord.Member, voice_channel: discord.VoiceChannel):
        """
        Handle the event when a member leaves a voice channel.
        """
        game_voice_channel = self.__get_channel(voice_channel.id)
        if game_voice_channel is None:
            return
        
        await game_voice_channel.on_left_member(member)

    async def on_join_member(self, member: discord.Member, voice_channel: discord.VoiceChannel):
        """
        Handle the event when a member joins a voice channel.
        """
        game_voice_channel = self.__get_channel(voice_channel.id)
        if game_voice_channel is None:
            if voice_channel.category is None:
                return

            setting = ChannelSettings().get_channel_setting(voice_channel.category.id)
            if setting is None:
                return

            game_voice_channel = self.__add_channel(GameVoiceChannel(voice_channel, setting))
        
        await game_voice_channel.on_join_member(member)

    def get_channel(self, channel_id: int):
        return self.__get_channel(channel_id)