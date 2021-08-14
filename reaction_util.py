from typing import Union

import discord

import bot_util
import embed_util


async def add_tick(msg: discord.Message):
    await msg.add_reaction(bot_util.EMOJI_TICK)


async def remove_tick(msg: discord.Message, client):
    await msg.remove_reaction(bot_util.EMOJI_TICK, await msg.guild.fetch_member(client.user.id))


def register_commands(client):
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

        if embed.title == bot_util.TITLE_JOIN_REQUEST:
            # single user wants to join a voice channel
            target_member = await message.guild.fetch_member(
                int(embed.description.split("<@")[1].split(">")[0])
            )
            who: str = embed.fields[0].value
            target_channel: Union[None, discord.VoiceChannel] = None
            if who == bot_util.TEXT_ACCEPT_ANYONE:
                # anyone can accept the request
                target_channel = bot_util.get_member_voice_channel(member)
            elif who.startswith(bot_util.TEXT_ACCEPT_ANYONE_CHANNEL):
                # anyone in the channel can accept
                accept_ch_id = int(who.split(bot_util.TEXT_ACCEPT_ANYONE_CHANNEL + "<#")[1][:-1])
                target_channel = bot_util.get_member_voice_channel(member, accept_ch_id)
            else:
                accept_ids = [int(x[2:-1]) for x in who.split("\n")]
                if member.id not in accept_ids:
                    return
                target_channel = bot_util.get_member_voice_channel(member)
            if target_channel is None:
                return
            await remove_tick(message, client)
            current_channel = bot_util.get_member_voice_channel(target_member)
            # TODO DM accept candidates
            if current_channel is None:
                return await embed_util.edit_join_embed(message, member, error="Requester is not connected!")
            if current_channel.id == target_channel.id:
                return await embed_util.edit_join_embed(message, member, error="Requester is already there!")
            await target_member.move_to(target_channel)
            await embed_util.edit_join_embed(message, member, target_channel=target_channel)
        elif embed.title == bot_util.TITLE_MOVE_REQUEST:
            # TODO permission check
            await remove_tick(message, client)
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
            await embed_util.edit_move_embed(message, member, success_ids, fail_ids)
