import discord
from discord_slash import SlashContext, SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

import bot_util
import embed_util


def register_commands(slash):

    @slash.subcommand(
        base="move",
        name="us",
        guild_ids=bot_util.SLASH_GUILD_IDS,
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
        src_channel: discord.VoiceChannel = bot_util.get_member_voice_channel(send_member)
        if not src_channel:
            return await ctx.send("You must be in a voice channel to do that")
        await embed_util.send_move_embed(ctx, src_channel.members, channel)

    # TODO add move commands
    # /move member <member> <channel>
    # /move channel <channel> <channel>
    # /move us <channel>  --> DONE
    # /move everyone <channel>
