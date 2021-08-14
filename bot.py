import os

import discord
from discord.ext import commands
from discord_slash import SlashCommand

import commands_join
import commands_move
import reaction_util

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # await client.change_presence(
    # activity=discord.Activity(type=discord.ActivityType.watching, name="Jackbox results"))

commands_join.register_commands(slash)
commands_move.register_commands(slash)
reaction_util.register_commands(client)


if __name__ == "__main__":
    client.run(os.environ.get("DISCORD_TOKEN"))
