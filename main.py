from discord.ext import commands
from discord import app_commands, FFmpegPCMAudio
import discord
import yt_dlp
import os
import asyncio
import traceback
import json
import requests
import time
import yt_dlp
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()


Client = MongoClient(os.getenv("mongodb"))
database = Client["Synapse"]
users = database["users"]

#? load bot config
with open("BotSettings.json", "r") as SettingsFile:
    BotConfig = json.load(SettingsFile)


bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), description="idk", owner_id=948646639961255936)


@bot.event
async def on_message(message: discord.Message):
    
    if message.author.bot:
        return
    userID = int(message.author.id)
    username = str(message.author.name)
    
    for unwantedlink in BotConfig["unwantedlinks"]:
        if unwantedlink in message.content:
            await message.delete()
            break
    

        

    users.update_one(
        {"_id": userID},
        {
            "$set": {
                "level": 1,
                "username": username,
                "nword": 0
            },
            "$inc": {"xp": 5}
        },
        upsert=True
    )
    for nword in BotConfig["nwords"]:
        if nword in message.content:
            users.update_one(
                {"_id": message.author.id},
                {"$inc": {"nword": 1}}
            )
    if users.find_one({"_id": message.author.id})["xp"] >= 100:
        users.update_one(
            {"_id": message.author.id},
            {
                "$inc": {"level": 1},
                "$set": {"xp": 0}
            },
        )
        levelup_embed = discord.Embed(
            title="**Level UP!**",
            description=f"{message.author.mention}, has leveled up to level {users.find_one({'_id': message.author.id})['level']}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        levelup_embed.set_author(
            name="Synapse", 
            icon_url=bot.user.avatar.url
        )
        levelup_embed.set_footer(
            text=f"level up embed, made by Synapse and its dev 'Kulisekxd'"
        )
        levelup_embed.set_image(
            url=message.author.avatar.url
        )
        await bot.get_channel(1467122073632637050).send(embed=levelup_embed)
    await bot.process_commands(message)









@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot is ready!")




@bot.tree.command(name="play", description="Play music")
async def play(interaction:discord.Interaction, url: str = None):
    
    if BotConfig["testingmode"] is True:
        if interaction.channel.id != 1457378020817113162:
            await interaction.followup.send("bot is in testing mode, request access in <#1466807521741111297>")
            return
    
    
    #? if no url is specified kindly KINDLY ask the user to specify one
    if not url:
        return await interaction.response.send_message("Specify url!")
    
    bot_vc_client = interaction.guild.voice_client

    
    
    if not interaction.user.voice:
        return await interaction.response.send_message("you must be in a voice channel to use voice chat related commands!")
    
    
    if url.startswith("http://"):
        return await interaction.response.send_message("Unsecure sites aren't allowed! check your link and make sure it has https://")
    if bot_vc_client:
        isplaying = interaction.guild.voice_client.is_playing()
            
        if isplaying:
            return await interaction.response.send_message("Synapse is already playing something.")
        
        if url.startswith("https://"):
            opts = {
                "outtmpl": "downloads/%(title)s.%(ext)s",
                "noplaylist": True,
                "format": "bestaudio/best",
                "cookiefile": "cookies.txt",
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                },
                "http_headers": {
                    "User-Agent": "Mozilla/5.0"
                },
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }


            await interaction.response.defer()
            with yt_dlp.YoutubeDL(opts) as ydl:
                music_history = bot.get_channel(1466502627360505968)
                Video_info = ydl.extract_info(url, download=False)
                title = Video_info.get("title")
                Uploader = Video_info.get("uploader")
                duration = Video_info.get("duration")
                duration_mins = duration // 60
                filepath = ydl.prepare_filename(Video_info)
                thumbnail = Video_info.get("thumbnail")
                ydl.download([url])
                embed = discord.Embed(
                    title="Now playing...",
                    description=f"**{title}**",
                    color=discord.Color.blurple()
                )

                embed.add_field(name="Uploader", value=Uploader, inline=True)
                embed.add_field(name="Duration (seconds)", value=str(duration), inline=True)
                embed.add_field(name="Duration (minutes)", value=str(duration_mins), inline=True)
                embed.add_field(name="Requester", value=interaction.user.mention, inline=False)
                embed.set_image(url=thumbnail)
                await music_history.send(embed=embed)
                bot_vc_client.play(FFmpegPCMAudio(filepath))
        else:
            return await interaction.followup.send("The URL is invalid, Example of link: 'https://link.com/ID'")
    else:
        return await interaction.followup.send("the bot isn't in a voice channel")
        





@bot.tree.command(name="join", description="Join a channel")
async def join(i: discord.Interaction):
    if BotConfig["testingmode"] is True:
        if i.channel.id != 1457378020817113162:
            await i.response.send_message("bot is in testing mode, request access to <#1457378020817113162> in <#1466807521741111297>")
            return
    
    if i.user.bot:
        return
    
    if i.user.voice.channel:
        bot_vc_client = await i.user.voice.channel.connect()
        bot_vc_client.play(FFmpegPCMAudio("greet.mp3"))
        
        await i.response.send_message("connected successfully without issues")
    else:
        await i.response.send_message("you aren't connected to a voice channel!")
    
    if bot_vc_client:
        return await i.response.send_message("Synapse is already connected to a channel!")
    
        
@bot.tree.command(name="pause", description="Pause currently playing music")
async def pause(i: discord.Interaction):
    if BotConfig["testingmode"] is True:
        if i.channel.id != 1457378020817113162:
            await i.response.send_message("bot is in testing mode, request access in <#1466807521741111297>")
            return
    if i.user.bot:
        return
    bot_vc_client = i.guild.voice_client
    if i.user.voice.channel:
        if bot_vc_client:   
            if bot_vc_client.is_playing(): 
                if bot_vc_client.is_paused():
                    return await i.followup.send("Synapse is already paused so there isn't anything to pause or there isn't anything playing.")
                bot_vc_client.pause()
            else:
                return await i.followup.send("Synapse isn't playing anything.")
        else:
            return await i.followup.send("Synapse isn't in a voice channel!")
    return await i.followup.send("you must be in a voice channel to use voice chat related commands!")


@bot.tree.command(name="resume", description="resume currently playing music")
async def resume(i: discord.Interaction):
    if BotConfig["testingmode"] is True:
        if i.channel.id != 1457378020817113162:
            await i.response.send_message("bot is in testing mode, request access in <#1466807521741111297>")
            return
    if i.user.bot:
        return
    bot_vc_client = i.guild.voice_client
    if i.user.voice.channel:
        if bot_vc_client:   
            if not bot_vc_client.is_playing(): 
                if not bot_vc_client.is_paused():
                    return await i.followup.send("nothing to resume since there is not anything paused bruh nga.")
                bot_vc_client.resume()
            else:
                return await i.followup.send("Synapse isn't playing anything.")
        else:
            return await i.followup.send("Synapse isn't in a voice channel!")
    else:
        return await i.followup.send("you must be in a voice channel to use voice chat related commands!")




@bot.tree.command(name="leave", description="leave the channel")
async def leave(i: discord.Interaction):
    bot_vc_client = i.guild.voice_client
    

    if i.user.voice.channel:
        if bot_vc_client:   
            await bot_vc_client.disconnect()
            await i.followup.send("Successfully left without issues")
        else:
            return await i.followup.send("Synapse isn't in a voice channel!")
    else:
        return await i.followup.send("you must be in a voice channel to use voice chat related commands!")

@bot.tree.command(name="stop", description="stop what's playing")
async def stop(i: discord.Interaction):
    bot_vc_client = i.guild.voice_client
    
    if i.user.bot:
        return
    if i.user.voice.channel:
        if bot_vc_client:   
            bot_vc_client.stop()
            await i.followup.send("stopped.")
        else:
            return await i.followup.send("Synapse isn't in a voice channel!")
    else:
        return await i.followup.send("you must be in a voice channel to use voice chat related commands!")


@bot.event
async def on_member_join(member:discord.Member):
    join_embed = discord.Embed(
        title="**New member**",
        description=f"{member.name} has joined us!",
        timestamp=discord.utils.utcnow(),
        color=discord.Color.greyple(),
    )
    join_embed.set_author(
        name="Synapse",
        icon_url=bot.user.avatar.url
    )
    join_embed.set_image(
        url=member.avatar.url
    )
    join_embed.set_footer(
        text=f"Welcome embed, made by Synapse and its dev 'Kulisekxd'"
    )
    join_channel = bot.get_channel(1352971409588224030)
    await join_channel.send(embed=join_embed)


@bot.event
async def on_member_remove(member:discord.Member):
    leave_embed = discord.Embed(
        title="**Member Left**",
        description=f"{member.name} has left us!",
        timestamp=discord.utils.utcnow(),
        color=discord.Color.red(),
    )
    leave_embed.set_author(
        name="Synapse",
        icon_url=bot.user.avatar.url
    )
    leave_embed.set_image(
        url=member.avatar.url
    )
    leave_embed.set_footer(
        text=f"Leave embed, made by Synapse and its dev 'Kulisekxd'"
    )
    join_channel = bot.get_channel(1352971409588224030)
    await join_channel.send(embed=leave_embed)



@bot.tree.command(name="level", description="show your or another user's current level")
async def level(i:discord.Interaction, user: discord.Member = None):
    if user is None:
        UserID = int(i.user.id)
    else:
        UserID = int(user.id)
    
    userXP = users.find_one({"_id": UserID})
    
    final_embed = discord.Embed(
        title=f"**{i.user.name}'s level**",
        description=f"{i.user.name}'s current xp and level is "
    )
    
@bot.tree.command(name="nwordleaderboard", description="shows the nword leaderboard")
async def NwordLeaderboard(i: discord.Interaction):
    sorted_nwords = users.find().sort("nword", -1).to_list()
    
    nwords_embed = discord.Embed(
        title="Nwords Leaderboard",
        description=f"This shows the most racist person on this server lol niggers \n the top niggest nigger is <@{sorted_nwords[0]['_id']}>",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )
    
    index = 0
    for _ in sorted_nwords:
        if index >= 5:
            break
        nwords_embed.add_field(name=f"{_['username']}", value=f"{_['nword']}", inline=False)
        index += 1
        
    await i.response.send_message(embed=nwords_embed)



@bot.tree.command(name="levelleaderboard", description="displays a level leaderboard")
async def levelleaderboard(i:discord.Interaction):
    sorted_levels = users.find().sort("level", -1).to_list()
    
    levels_embed = discord.Embed(
        title="levels Leaderboard",
        description=f"This shows a leaderboard on this server \n the top level currently is <@{sorted_levels[0]['_id']}>",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )
    
    index = 0
    for _ in sorted_levels:
        if index >= 5:
            break
        levels_embed.add_field(name=f"{_['username']}", value=f"{_['level']}", inline=False)
        index += 1
        
    await i.response.send_message(embed=levels_embed)




# ? bot running logic
try:
    bot.owner_id = BotConfig["OwnerID"]
    bot.command_prefix = BotConfig["CommandPrefix"]
    #? after config is loaded into bot, again, if no exception happened, run the bot.
    bot.run(token=os.getenv("tkn"), reconnect=BotConfig["Reconnect"])

#? if a exception happens, ill get output.
except Exception:
    WebhookData = {
        "content": f"Error while running bot. \n ```{traceback.format_exc()}```",
        "username":"Synapse Error Handler Webhook"
    }
    print(f"Error while running bot. \n ```{traceback.format_exc()}```")
    Send_Webhook = requests.post(url=os.getenv("webhook"), json=WebhookData)
    if Send_Webhook.status_code == 204:
        print("Sent webhook about error.")
        exit(1)
    else:
        print("Failed to send webhook, very likely discord's fault.")
        exit(1)

