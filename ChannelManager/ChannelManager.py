import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
intents.moderation = True
intents.voice_states = True  

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    modules = ["events.VoiceChannelEvents"]

    # Load cogs
    for module in modules:
        try:
            await bot.load_extension(module)
            print(f"Loaded module \"{module}\" successfully.")
        except Exception as e:
            print(f"Failed to load module \"{module}\". {e}")
   

    await bot.tree.sync()

# Launch bot
bot_token = os.getenv("CHANNEL_MANAGER_BOT_TOKEN")
if bot_token:
    bot.run(bot_token)
else:
    print("There is no CHANNEL_MANAGER_BOT_TOKEN!")