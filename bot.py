"""
author: @killamocingbird

"""
import os

import aiohttp
import aiofiles
import discord
from dotenv import load_dotenv
import random
import urllib.request

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_GUILD = os.getenv('TARGET_GUILD').strip()
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL').strip()

client = discord.Client()

@client.event
async def on_ready():
    # Find target guild
    in_target = False
    for guild in client.guilds:
        if guild.name == TARGET_GUILD:
            in_target = True
            break
        
    assert in_target, "bot not in target guild"
    
    channel_exists = False
    for channel in guild.channels:
        if channel.name == TARGET_CHANNEL:
            channel_exists = True
            break
        
    assert channel_exists, "target channel does not exist"
    
    print("Bot startup successful")
    
@client.event
async def on_message(message):
    # Ignore bot sent messages
    if message.author == client.user:
        return

    # Only react to message in the target channel
    if message.channel.name.strip() != TARGET_CHANNEL:
        return
    
    # Download each attachment
    for attachment in message.attachments:
        url = attachment.url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    f = await aiofiles.open(url.split('/')[-1], mode='wb')
                    await f.write(await r.read())
                    await f.close()



client.run(TOKEN)
