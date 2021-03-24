"""
author: @killamocingbird

"""
import os
import pickle

import aiohttp
import aiofiles
import discord
from dotenv import load_dotenv

import ftplib

# Error messages
FTP_NOT_CONFIG = "FTP is not configured. Please type in ```SB host {host}```" \
                "```SB login {login username}``````SB pass {password}```" \
                "```SB dest {ftp schematic file destination}``` to configure. "\
                "Afterwards please type ```SB confirm```"

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_GUILD = os.getenv('TARGET_GUILD').strip()
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL').strip()
DESTINATION = os.getenv('DESTINATION')

FTP_INFO = {'host': None, 'login': None, 'pass': None, 'dest': None}
if os.path.isfile('FTP_INFO.pickle'):
    FTP_INFO = pickle.load(open('FTP_INFO.pickle', 'rb')) 
pickle.dump(FTP_INFO, open('FTP_INFO.pickle', 'wb'))

FTP = None

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
    
    try:
        FTP = ftplib.FTP(FTP_INFO['host'])
        await channel.send(FTP.login(FTP_INFO['login'], FTP_INFO['pass']))
        await channel.send(FTP.cwd(FTP_INFO['dest']))
        FTP.quit()
    except:
        await channel.send(FTP_NOT_CONFIG)
    
    print("Bot startup successful")
    
@client.event
async def on_message(message):
    # Ignore bot sent messages
    if message.author == client.user:
        return
    
    # Only react to message in the target guild and channel
    if message.guild.name.strip() != TARGET_GUILD or message.channel.name.strip() != TARGET_CHANNEL:
        return
    
    if ((FTP_INFO['host'] is None or FTP_INFO['login'] is None or FTP_INFO['pass'] is None or FTP_INFO['dest'] is None) 
        and 'SB' != message.content[:2]):
        await message.channel.send(FTP_NOT_CONFIG)
    
    elif 'SB' == message.content[:2]:
        command = message.content.split(' ')[1]
        if command.lower() == 'host' or command.lower() == 'login' or command.lower() == 'pass' or command.lower() == 'dest':
            FTP_INFO[command.lower()] = message.content.split(' ')[2]
            pickle.dump(FTP_INFO, open('FTP_INFO.pickle', 'wb'))
        elif command.lower() == 'confirm':
            for v in FTP_INFO.values():
                if v is None:
                    await message.channel.send("Not all FTP values are set.")
            try:
                FTP = ftplib.FTP(FTP_INFO['host'])
                await message.channel.send(FTP.login(FTP_INFO['login'], FTP_INFO['pass']))
                await message.channel.send(FTP.cwd(FTP_INFO['dest']))
                FTP.quit()
            except:
                await message.channel.send("Error with FTP, please check values.")
        else:
            await message.channel.send("Unknown command %s. Please use ```host```" \
                                       "```login``` ```pass``` ```confirm```" % command)
    else:
        # Download each attachment
        for attachment in message.attachments:
            url = attachment.url
            # Skip non schematic files
            if url.split('.')[-1] != 'schematic':
                continue
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        filename = url.split('/')[-1]
                        f = await aiofiles.open('temp', mode='wb')
                        await f.write(await r.read())
                        await f.close()
                        
                        # Open file
                        f = open('temp', 'rb')
                        FTP = None
                        try:
                            FTP = ftplib.FTP(FTP_INFO['host'])
                            FTP.login(FTP_INFO['login'], FTP_INFO['pass'])
                            FTP.cwd(FTP_INFO['dest'])
                        except:
                            await message.channel.send("Error with FTP, please check values.")
                            FTP.quit()
                            continue
                        try:
                            FTP.storbinary("STOR " + filename, f)
                            await message.channel.send("File %s successfully uploaded" % filename)
                        except:
                            await message.channel.send("File %s failed to upload" % filename)
                        if FTP is not None:
                            FTP.quit()
        
        



client.run(TOKEN)
