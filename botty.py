# botty mcbotface
from discord.ext import commands
import sys
from pathlib import Path
import yaml

# Set our API key
api_name = os.path.expanduser('~/.rcc-api')
api_token = Path(api_name).read_text()

# Dynamically load in our magic config files
config_name = os.path.expanduser('~/.rcc-tools.yml')
config = yaml.safe_load(open(config_name))
discord_bot_token = config["discord_bot_token"]

description = '''TEST Bot'''
bot = commands.Bot(command_prefix='!', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.command()
async def send_message(ctx):
    await ctx.send(discord_message)

bot.run(discord_bot_token)