from datetime import datetime
import json
import os
from typing import Union

import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)

SLASH_GUILD_IDS = None
if os.environ.get("SLASH_GUILD_IDS"):
    SLASH_GUILD_IDS = json.loads(os.environ.get("SLASH_GUILD_IDS"))
TITLE_JOIN_REQUEST = "Join request"
TITLE_MOVE_REQUEST = "Move request"
TEXT_ACCEPT_ANYONE = "anyone ^-^"
TEXT_ACCEPT_ANYONE_CHANNEL = "Anyone in channel "
EMOJI_TICK = "✅"
EMPTY_EMBED = dict.fromkeys(("name", "value"), "\u200b")


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # await client.change_presence(
    # activity=discord.Activity(type=discord.ActivityType.watching, name="Jackbox results"))


@slash.subcommand(
    base="join",
    name="user",
    guild_ids=SLASH_GUILD_IDS,
    options=[
                create_option(
                    name="user",
                    description="user to join",
                    required=True,
                    option_type=SlashCommandOptionType.USER
                )
            ] + [
                create_option(
                    name="user" + str(x + 1),
                    description="user to join",
                    required=False,
                    option_type=SlashCommandOptionType.USER
                ) for x in range(1, 5)
            ]
)
async def cmd_join_user(ctx: SlashContext, *, user, **kwargs):
    print("subcommand called!")
    print("user:", user)
    print("additional users:", kwargs)
    members = [user]
    for key, value in kwargs.items():
        if key.startswith("user"):
            members.append(value)
    await send_join_embed(ctx, members=members)


@slash.subcommand(
    base="join",
    name="channel",
    guild_ids=SLASH_GUILD_IDS,
    options=[
        create_option(
            name="channel",
            description="channel to join",
            required=True,
            option_type=SlashCommandOptionType.CHANNEL
        )
    ]
)
async def cmd_join_channel(ctx: SlashContext, channel):
    if not isinstance(channel, discord.VoiceChannel) or isinstance(channel, discord.StageChannel):
        await ctx.send("Umm, that's not a joinable channel")
        return
    await send_join_embed(ctx, channel=channel)


@slash.subcommand(
    base="join",
    name="anywhere",
    guild_ids=SLASH_GUILD_IDS
)
async def cmd_join_anywhere(ctx: SlashContext):
    await send_join_embed(ctx)


# === move commands === #

@slash.subcommand(
    base="move",
    name="us",
    guild_ids=SLASH_GUILD_IDS,
    options=[
        create_option(
            name="channel",
            description="channel to move to",
            required=True,
            option_type=SlashCommandOptionType.CHANNEL
        )
    ]
)
async def cmd_move_us(ctx: SlashContext, channel):
    if not isinstance(channel, discord.VoiceChannel) or isinstance(channel, discord.StageChannel):
        await ctx.send("Umm, that's not a joinable channel")
        return
    send_member = await ctx.guild.fetch_member(ctx.author_id)
    src_channel: discord.VoiceChannel = get_member_voice_channel(send_member)
    if not src_channel:
        return await ctx.send("You must be in a voice channel to do that")
    await send_move_embed(ctx, src_channel.members, channel)


# TODO add move commands
# /move member <member> <channel>
# /move channel <channel> <channel>
# /move us <channel>  --> DONE
# /move everyone <channel>


async def add_tick(msg: discord.Message):
    await msg.add_reaction(EMOJI_TICK)


async def remove_tick(msg: discord.Message):
    await msg.remove_reaction(EMOJI_TICK, await msg.guild.fetch_member(client.user.id))


def get_member_voice_channel(member: discord.Member, match_channel_id=None):
    voice_state = member.voice
    if not voice_state:
        return None
    voice_state_channel = voice_state.channel
    if match_channel_id is not None and voice_state_channel.id != match_channel_id:
        return None
    return voice_state_channel


def format_member_list(*_, ids=None, members=None):
    if ids is None and members is None:
        return None
    if members and not ids:
        ids = [m.id for m in members]
    return " ".join(f"<@{id_}>" for id_ in ids)


async def send_move_embed(ctx: SlashContext, members, channel):
    # move <members> to <channel>
    embed = discord.embeds.Embed(
        title=TITLE_MOVE_REQUEST,
        description=f"<@{ctx.author_id}> wants to move {len(members)} {'person' if len(members) == 1 else 'people'}!"
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="Target", value=f"<#{channel.id}>", inline=True)
    embed.add_field(name="Who can Accept", value="Admins & Moderators", inline=True)
    embed.add_field(name="Affected Users", value=format_member_list(members=members), inline=False)
    msg = await ctx.send(embed=embed)
    await add_tick(msg)


async def send_join_embed(ctx: SlashContext, members=None, channel=None):
    embed = discord.embeds.Embed(
        title=TITLE_JOIN_REQUEST,
        description=f"<@{ctx.author_id}> is asking to join a voice channel!"
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    if members is None and channel is None:
        accepters = TEXT_ACCEPT_ANYONE
    elif members is not None:
        accepters = "\n".join(map(lambda x: f"<@{x.id}>", members))
    elif channel is not None:
        accepters = f"{TEXT_ACCEPT_ANYONE_CHANNEL}<#{channel.id}>"
    else:
        # channel and users defined - something went wrong
        await ctx.send(
            "something went wrong. check your command syntax and try again later.\n(cc <@346668804375445505>)"
        )
        return
    embed.add_field(
        name="Who can accept",
        value=accepters
    )
    msg = await ctx.send(embed=embed)
    await add_tick(msg)


def make_editable_embed(old_embed: discord.embeds.Embed):
    embed = discord.Embed(title=old_embed.title, description=old_embed.description, timestamp=datetime.utcnow())
    # noinspection PyProtectedMember
    embed._author = old_embed._author
    return embed


async def edit_join_embed(message: discord.Message, accept_member: discord.Member, *, target_channel=None, error=None):
    embed = make_editable_embed(message.embeds[0])
    embed.add_field(name="Accepted By", value=f"<@{accept_member.id}>")
    # embed.add_field(**EMPTY_EMBED)
    if target_channel is not None:
        embed.add_field(name="Moved To", value=f"<#{target_channel.id}>")
        embed.set_footer(text="Success!")
    else:
        embed.add_field(name="Error", value=error or "unknown error")
        embed.set_footer(text="Something went wrong :(")
    await message.edit(embed=embed)


async def edit_move_embed(message: discord.Message, accept_member: discord.Member, success_ids=None, fail_ids=None):
    embed = make_editable_embed(message.embeds[0])
    embed.add_field(name="Target", value="foo")  # TODO
    embed.add_field(name="Accepted By", value=f"<@{accept_member.id}>")
    success_str = format_member_list(ids=success_ids) or "nobody"
    fail_str = format_member_list(ids=fail_ids) or "nobody"
    embed.add_field(name="Moved", value=success_str, inline=False)
    embed.add_field(name="Not Moved", value=fail_str, inline=False)
    embed.set_footer(text=(
        f"{0 if not success_ids else len(success_ids)} Moved, "
        f"{0 if not fail_ids else len(fail_ids)} Not Moved"
    ))
    await message.edit(embed=embed)


@client.event
async def on_raw_reaction_add(payload: discord.raw_models.RawReactionActionEvent):
    # TODO add support for denying (cross emoji)
    if payload.user_id == client.user.id:
        return
    channel: discord.TextChannel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if message.author.id != client.user.id:
        return
    if not isinstance(payload.emoji, discord.PartialEmoji):
        return
    emoji: discord.PartialEmoji = payload.emoji
    existing_reaction = [x for x in message.reactions if x.emoji == emoji.name]
    if len(existing_reaction) != 1 or not existing_reaction[0].me:
        return
    if len(message.embeds) != 1:
        return
    embed: discord.Embed = message.embeds[0]
    user: discord.User = await client.fetch_user(payload.user_id)
    member: discord.Member = await message.guild.fetch_member(payload.user_id)

    if embed.title == TITLE_JOIN_REQUEST:
        # single user wants to join a voice channel
        target_member = await message.guild.fetch_member(
            int(embed.description.split("<@")[1].split(">")[0])
        )
        who: str = embed.fields[0].value
        target_channel: Union[None, discord.VoiceChannel] = None
        if who == TEXT_ACCEPT_ANYONE:
            # anyone can accept the request
            target_channel = get_member_voice_channel(member)
        elif who.startswith(TEXT_ACCEPT_ANYONE_CHANNEL):
            # anyone in the channel can accept
            accept_ch_id = int(who.split(TEXT_ACCEPT_ANYONE_CHANNEL + "<#")[1][:-1])
            target_channel = get_member_voice_channel(member, accept_ch_id)
        else:
            accept_ids = [int(x[2:-1]) for x in who.split("\n")]
            if member.id not in accept_ids:
                return
            target_channel = get_member_voice_channel(member)
        if target_channel is None:
            return
        await remove_tick(message)
        current_channel = get_member_voice_channel(target_member)
        # TODO DM accept candidates
        if current_channel is None:
            return await edit_join_embed(message, member, error="Requester is not connected!")
        if current_channel.id == target_channel.id:
            return await edit_join_embed(message, member, error="Requester is already there!")
        await target_member.move_to(target_channel)
        await edit_join_embed(message, member, target_channel=target_channel)
    elif embed.title == TITLE_MOVE_REQUEST:
        # TODO permission check
        await remove_tick(message)
        target_channel: discord.VoiceChannel = await client.fetch_channel(int(embed.fields[0].value[2:-1]))
        affected_members = [
            await target_channel.guild.fetch_member(int(snowflake[2:-1]))
            for snowflake in embed.fields[2].value.split()
        ]
        success_ids = []
        fail_ids = []
        for mem in affected_members:
            try:
                await mem.move_to(target_channel)
                success_ids.append(mem.id)
            except discord.errors.HTTPException:
                fail_ids.append(mem.id)
        await edit_move_embed(message, member, success_ids, fail_ids)


if __name__ == "__main__":
    client.run(os.environ.get("DISCORD_TOKEN"))
