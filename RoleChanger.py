import discord
import aiohttp
import asyncio
import time
import json
from discord.ext import commands
from discord.utils import find, get

bot_token = ""
riot_key = ""
match_count = 5
update_timer = 600 #seconds
first = True

bot = commands.Bot(command_prefix='/')

@bot.event
async def on_ready():
    global first
    if first:
        await update_roles()
        first = False

@bot.command()
async def update(ctx):
    await update_roles()

@bot.command()
async def shutdown(ctx):
    with open("players.txt", "w") as file:
        json.dump(players, file)
    print("Shutting down")
    await bot.logout()

@bot.command()
async def add(ctx):
    if ctx.author.id not in players.values():
        players[ctx.message.content[5:]] = ctx.author.id
        await ctx.channel.send("League user " + ctx.message.content[5:] + " added to the system - use /remove to remove")
    else:
        await ctx.channel.send("There is already a League account linked to this Discord account - use /remove first")
    await update_roles()

@bot.command()
async def remove(ctx):
    for name, discord_id in players.items():
        if discord_id == ctx.author.id:
            del players[name]
            await ctx.channel.send("League user " + name + " has been removed - add a new one with /add summonerName")
            await update_roles()
            return
    await ctx.channel.send("You have no accounts linked - add a new one with /add summonerName")
    await update_roles()
            

async def get_last_match(player):
    results = []
    url = "https://euw1.api.riotgames.com/"
    summoner = await api_request(url + "lol/summoner/v4/summoners/by-name/" + player + "?api_key=" + riot_key)
    last_games = await api_request(url + "lol/match/v4/matchlists/by-account/" + summoner["accountId"] + "?endIndex=" + str(match_count) + "&api_key=" + riot_key)
    for game in last_games["matches"]:
        result = await api_request(url + "lol/match/v4/matches/" + str(game["gameId"]) + "?api_key=" + riot_key)
        for participant in result["participantIdentities"]:
            if participant["player"]["summonerName"] == player:
                participant_id = participant["participantId"]
                if participant_id <= 5:
                    teamId = 0
                else:
                    teamId = 1 
                break

        results.append(result["teams"][teamId]["win"])
    return results

async def api_request(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                return await r.json()

async def update_roles():
    print("Updating..." + str(time.localtime()[3]) + ":" + str(time.localtime()[4]))
    for player in players:
        discord_id = players[player]
        member = find(lambda m: m.id == discord_id, bot.get_all_members())
        if member:
            result = await get_last_match(player)
            planinec = member.guild.get_role(615889238780674051)
            padalec = member.guild.get_role(618081721488900115)
            if result.count("Win") >= 3:
                await member.add_roles(planinec)
                await member.remove_roles(padalec)
            else:
                await member.add_roles(padalec)
                await member.remove_roles(planinec)
            print("Player " + player + " updated!")
        time.sleep(1)
    print("Waiting! \n")
    await asyncio.sleep(update_timer)
    await update_roles()

with open("players.txt") as file:
    global players
    players = json.load(file)
    print(players)
    
bot.run(bot_token)


