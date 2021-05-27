#!/usr/bin/python3
# Thanks L and P from Discord Python, you know who you are.
import os
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

print(discord_bot_token)
# Check if the config is empty
if config is None:
    print("Failed to load configuration.")
    sys.exit(1338)
# bot.py
import discord

class CustomClient(discord.Client):
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')

    async def fire_message(message):
        print('message!!')

client = CustomClient()
client.run(discord_bot_token)

print("HELLO")
CustomClient.fire_message()

async def hello_world():
    channel = self.get_channel(810756597546614834)  # channel ID goes here
    await channel.send("hello world! <333")