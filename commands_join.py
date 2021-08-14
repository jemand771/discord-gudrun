import discord
from discord_slash import SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

import bot_util
import embed_util


def register_commands(slash):
    @slash.subcommand(
        base="join",
        name="user",
        guild_ids=bot_util.SLASH_GUILD_IDS,
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
        await embed_util.send_join_embed(ctx, members=members)

    @slash.subcommand(
        base="join",
        name="channel",
        guild_ids=bot_util.SLASH_GUILD_IDS,
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
        await embed_util.send_join_embed(ctx, channel=channel)

    @slash.subcommand(
        base="join",
        name="anywhere",
        guild_ids=bot_util.SLASH_GUILD_IDS
    )
    async def cmd_join_anywhere(ctx: SlashContext):
        await embed_util.send_join_embed(ctx)
