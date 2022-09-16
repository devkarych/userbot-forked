__all__ = [
    "commands",
]

import logging
import random

from pyrogram import Client
from pyrogram.errors import MsgIdInvalid, ReactionEmpty, ReactionInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..constants import Icons
from ..modules import CommandObject, CommandsModule

commands = CommandsModule("Reactions")
_log = logging.getLogger(__name__)


@commands.add("r", usage="<reply> [emoji]")
async def put_reaction(_: Client, message: Message, command: CommandObject) -> str | None:
    """Reacts to a message with a specified emoji or removes any reaction"""
    reaction = command.args
    try:
        await message.reply_to_message.react(reaction)
    except ReactionInvalid:
        return reaction
    except ReactionEmpty:
        pass  # ignore
    await message.delete()


@commands.add("rs", usage="<reply>")
async def get_reactions(client: Client, message: Message, __: CommandObject) -> str:
    """Gets message reactions with users who reacted to it"""
    chat_peer = await client.resolve_peer(message.chat.id)
    t = ""
    try:
        messages: types.messages.MessageReactionsList = await client.invoke(
            functions.messages.GetMessageReactionsList(
                peer=chat_peer,
                id=message.reply_to_message.id,
                limit=100,
            )
        )
    except MsgIdInvalid:
        icon = Icons.WARNING.get_icon(client.me.is_premium)
        return f"{icon} <i>Message not found or has no reactions</i>"
    reactions: dict[int | str, set[int]] = {}
    for r in messages.reactions:
        if isinstance(r.reaction, types.ReactionCustomEmoji):
            reaction = r.reaction.document_id
        elif isinstance(r.reaction, types.ReactionEmoji):
            reaction = r.reaction.emoticon
        else:
            _log.warning(
                "Empty reaction found! (msg_id=%r, chat_id=%r)",
                message.reply_to_message.id,
                message.chat.id,
            )
            continue
        reactions.setdefault(reaction, set()).add(r.peer_id.user_id)
    for reaction, peers in reactions.items():
        if isinstance(reaction, int):
            if client.me.is_premium:
                reaction_str = f"<emoji id={reaction}>⁉</emoji>"
            else:
                reaction_str = f"Custom reaction #<code>{reaction}</code>"
        else:
            reaction_str = reaction
        t += f"{reaction_str}: {len(peers)}\n"
        for peer_id in peers:
            for user in messages.users:
                if user.id == peer_id:
                    peer_name = user.first_name or "Deleted Account"
                    break
            else:
                peer_name = "Unknown user"
            t += f"- <a href='tg://user?id={peer_id}'>{peer_name}</a> (#<code>{peer_id}</code>)\n"
    return t or f"{Icons.WARNING.get_icon(client.me.is_premium)} <i>No reactions here</i>"


@commands.add("rr", usage="<reply>")
async def put_random_reaction(client: Client, message: Message, _: CommandObject) -> None:
    """Reacts to a message with a random available emoji"""
    chat = await client.get_chat(message.chat.id)
    await message.reply_to_message.react(random.choice(chat.available_reactions))
    await message.delete()
