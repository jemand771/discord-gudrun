from datetime import datetime

import discord
from discord_slash import SlashContext

import bot_util
import reaction_util


async def send_move_embed(ctx: SlashContext, members, channel):
    # move <members> to <channel>
    embed = discord.embeds.Embed(
        title=bot_util.TITLE_MOVE_REQUEST,
        description=f"<@{ctx.author_id}> wants to move {len(members)} {'person' if len(members) == 1 else 'people'}!"
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="Target", value=f"<#{channel.id}>", inline=True)
    embed.add_field(name="Who can Accept", value="Admins & Moderators", inline=True)
    embed.add_field(name="Affected Users", value=bot_util.format_member_list(members=members), inline=False)
    msg = await ctx.send(embed=embed)
    await reaction_util.add_tick(msg)


async def send_join_embed(ctx: SlashContext, members=None, channel=None):
    embed = discord.embeds.Embed(
        title=bot_util.TITLE_JOIN_REQUEST,
        description=f"<@{ctx.author_id}> is asking to join a voice channel!"
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    if members is None and channel is None:
        accepters = bot_util.TEXT_ACCEPT_ANYONE
    elif members is not None:
        accepters = "\n".join(map(lambda x: f"<@{x.id}>", members))
    elif channel is not None:
        accepters = f"{bot_util.TEXT_ACCEPT_ANYONE_CHANNEL}<#{channel.id}>"
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
    await reaction_util.add_tick(msg)


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
    success_str = bot_util.format_member_list(ids=success_ids) or "nobody"
    fail_str = bot_util.format_member_list(ids=fail_ids) or "nobody"
    embed.add_field(name="Moved", value=success_str, inline=False)
    embed.add_field(name="Not Moved", value=fail_str, inline=False)
    embed.set_footer(text=(
        f"{0 if not success_ids else len(success_ids)} Moved, "
        f"{0 if not fail_ids else len(fail_ids)} Not Moved"
    ))
    await message.edit(embed=embed)
