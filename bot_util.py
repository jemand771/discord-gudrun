import json
import os

import discord

SLASH_GUILD_IDS = None
if os.environ.get("SLASH_GUILD_IDS"):
    SLASH_GUILD_IDS = json.loads(os.environ.get("SLASH_GUILD_IDS"))
TITLE_JOIN_REQUEST = "Join request"
TITLE_MOVE_REQUEST = "Move request"
TEXT_ACCEPT_ANYONE = "anyone ^-^"
TEXT_ACCEPT_ANYONE_CHANNEL = "Anyone in channel "
EMOJI_TICK = "✅"
EMPTY_EMBED = dict.fromkeys(("name", "value"), "\u200b")


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
