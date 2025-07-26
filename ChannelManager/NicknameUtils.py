from typing import Tuple
from discord import Member

spectator_prefix = "👀"
old_spectator_prefix = "観戦"

def is_spectator(member: Member):
    if member is None:
        return False

    if member.nick is None:
        return False
    if member.nick.startswith(spectator_prefix):
        return True
    return False

async def change_to_spectator(member: Member) -> Tuple[bool, str]:
    """
    Change the nickname of a member to a spectator format.
    
    Parameters:
        member (Member): The member whose nickname is to be changed.
    """

    try:
        if member.nick is None:
            await member.edit(nick=spectator_prefix + member.name)
            return [True, "名前を変更しました。"]

        if member.nick.startswith(spectator_prefix):
            if member.nick.startswith(old_spectator_prefix):
                await member.edit(nick=member.nick[len(old_spectator_prefix):])
            return [False, "既に観戦者になっています。"]

        old_nick = member.nick
        if old_nick.startswith(old_spectator_prefix):
            old_nick = old_nick[len(old_spectator_prefix):]
        await member.edit(nick=spectator_prefix + old_nick)
        return [True, "名前を変更しました。"]
    except Exception as e:
        return [False, "名前を変更できませんでした。\nサーバープロフィールを編集し、自身のニックネームの先頭に👀を付けてください。"]
        

async def change_to_player(member: Member) -> Tuple[bool, str]:
    try:
        if member.nick is None:
            return [False, "既に参加者になっています。"]

        nick = member.nick
        if nick is not None:
            while nick.startswith(spectator_prefix):
                nick = nick[len(spectator_prefix):]
            if len(nick) == 0 or nick == member.name:
                nick = None

        if nick == member.nick:
            return [False, "既に参加者になっています。"]

        await member.edit(nick=nick if len(nick) > 0 else None)
        return [True, "名前を変更しました。"]
    except Exception as e:
        return [False, "名前を変更できませんでした。\nサーバープロフィールを編集し、自身のニックネームの先頭から👀を取り除いてください。"]