#    This file is part of the AutoAnime distribution.
#    Copyright (c) 2024 Kaif_00z
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in <
# https://github.com/kaif-00z/AutoAnimeBot/blob/main/LICENSE > .

# if you are using this following code then don't forgot to give proper
# credit to t.me/kAiF_00z (github.com/kaif-00z)

import base64
import re
import json
import os

from AnilistPython import Anilist
from traceback import format_exc

from telethon import Button, events
from telethon.errors.rpcerrorlist import FloodWaitError

from core.bot import Bot
from core.executors import Executors
from database import DataBase
from functions.info import AnimeInfo
from functions.schedule import ScheduleTasks, Var
from functions.tools import Tools, asyncio
from functions.utils import AdminUtils
from libs.ariawarp import Torrent
from libs.logger import LOGS, Reporter
from libs.subsplease import SubsPlease
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
print("----------Starting Scheduler----------")
scheduler.start()
print("Scheduler started!")

def delete_files():
    directory = os.getcwd()
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

scheduler.add_job(restart, "interval", seconds=86400)
print("Added Files clean Scheduler for a day")

anilist = Anilist()
tools = Tools()
tools.init_dir()
bot = Bot()
dB = DataBase()
subsplease = SubsPlease(dB)
torrent = Torrent()
schedule = ScheduleTasks(bot)
admin = AdminUtils(dB, bot)


@bot.on(
    events.NewMessage(
        incoming=True, pattern="^/start ?(.*)", func=lambda e: e.is_private
    )
)
async def _start(event):
    xnx = await event.reply("`Please Wait...`")
    msg_id = event.pattern_match.group(1)
    await dB.add_broadcast_user(event.sender_id)
    if Var.FORCESUB_CHANNEL and Var.FORCESUB_CHANNEL_LINK:
        is_user_joined = await bot.is_joined(Var.FORCESUB_CHANNEL, event.sender_id)
        if is_user_joined:
            pass
        else:
            return await xnx.edit(
                f"**Please Join The Following Channel To Use This Bot 🫡**",
                buttons=[
                    [Button.url("🚀 JOIN CHANNEL", url=Var.FORCESUB_CHANNEL_LINK)],
                    [
                        Button.url(
                            "♻️ REFRESH",
                            url=f"https://t.me/{((await bot.get_me()).username)}?start={msg_id}",
                        )
                    ],
                ],
            )
    if msg_id:
        if msg_id.isdigit():
            msg = await bot.get_messages(Var.BACKUP_CHANNEL, ids=int(msg_id))
            await event.reply(msg)
        elif re.match(r'^DSTORE-', msg_id):
            await xnx.edit("Loading batch files....")
            b_string = msg_id.split("-", 1)[1]
            decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
            try:
                f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
            except ValueError:
                f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
                protect = "batch"

            # Get the range of message IDs to process
            f_msg_id, l_msg_id, f_chat_id = map(int, [f_msg_id, l_msg_id, f_chat_id])

            # Iterate through the message IDs from the first to the last
            for msg_id in range(f_msg_id, l_msg_id + 1):
                try:
                    msg = await bot.get_messages(Var.BACKUP_CHANNEL, ids=int(msg_id))
                    if not msg:
                        continue
                    await xnx.reply(msg)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                    await xnx.reply(msg)
                except Exception as e:
                    LOGS.error(e)
                    continue
                await asyncio.sleep(1)
        else:
            items = await dB.get_store_items(msg_id)
            if items:
                for id in items:
                    msg = await bot.get_messages(Var.CLOUD_CHANNEL, ids=id)
                    await event.reply(file=[i for i in msg])
    else:
        if event.sender_id == Var.OWNER:
            return await xnx.edit(
                "** <                ADMIN PANEL                 > **",
                buttons=admin.admin_panel(),
            )
        await event.reply(
            f"**Enjoy Ongoing Anime's Best Encode 24/7 🫡**",
            buttons=[
                [
                    Button.url("Join", url=Var.FORCESUB_CHANNEL_LINK),
                    Button.url(
                        "Bot Updates",
                        url="https://t.me/hybridupdates",
                    ),
                ]
            ],
        )
    await xnx.delete()

@bot.on(
    events.NewMessage(
        incoming=True,
        pattern=r"^/poster ?([\S\s]*)",
        func=lambda e: e.is_private
    )
)
async def poster_cmd(event):
    xnx = await event.reply("`Please Wait...`")
    msg_str = event.pattern_match.group(1).strip()

    if not msg_str:
        await xnx.edit("Usage: /poster <anime name>\nExample: `/poster demon slayer`")
        return

    try:
        aaa = anilist.get_anime_id(msg_str)
        await xnx.edit(f"✅ Anime found: `{msg_str}`\nAnilist ID: `{aaa}`\n\n**🪄 Generating Poster.....**")
        await bot.send_file(
            event.sender_id,
            file=f"https://img.anili.st/media/{aaa}"
        )
        await xnx.edit(f"✅ Poster Generated for: `{msg_str}`\nAnilist ID: `{aaa}`")
    except IndexError:
        await xnx.edit(f"⚠️ Anime not found: `{msg_str}`")


ADMINS = Var.OWNER
FILE_STORE_CHANNEL = Var.CLOUD_CHANNEL
LOG_CHANNEL = Var.LOG_CHANNEL

@bot.on(events.NewMessage(pattern=r'/link|/plink'))
async def gen_link_s(event):
    replied = await event.get_reply_message()

    if not replied:
        return await event.reply('Reply to a message to get a shareable link.')

    if not replied.media:
        return await event.reply("Reply to a supported media")

    # Check protected content
    if event.message.is_protected and event.chat_id not in ADMINS:
        return await event.reply("okDa")

    file_type = type(replied.media).__name__.lower()
    file_id, ref = unpack_new_file_id(getattr(replied, file_type).file.id)

    # Create the encoded string
    command = event.text.lower().strip()
    string = 'filep_' if command == "/plink" else 'file_'
    string += file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")

    me = await bot.get_me()
    U_NAME = f"{me.username}"
    await event.reply(f"Here is your Link:\nhttps://t.me/{U_NAME}?start={outstr}")

@bot.on(events.NewMessage(pattern=r'/batch|/pbatch'))
async def gen_link_batch(event):
    message_text = event.raw_text.strip()

    if " " not in message_text:
        return await event.reply("Use correct format.\nExample: /batch https://t.me/hybrid_movies/10 https://t.me/hybrid_movies/20")

    links = message_text.split(" ")

    if len(links) != 3:
        return await event.reply("Use correct format.\nExample: /batch https://t.me/hybrid_movies/10 https://t.me/hybrid_movies/20")

    cmd, first, last = links
    regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")

    match = regex.match(first)
    if not match:
        return await event.reply('Invalid link')

    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))

    if f_chat_id.isnumeric():
        f_chat_id = int("-100" + f_chat_id)

    match = regex.match(last)
    if not match:
        return await event.reply('Invalid link')

    l_chat_id = match.group(4)
    l_msg_id = int(match.group(5))

    if l_chat_id.isnumeric():
        l_chat_id = int("-100" + l_chat_id)

    if f_chat_id != l_chat_id:
        return await event.reply("Chat ids not matched.")

    try:
        chat = await bot.get_entity(f_chat_id)
    except Exception as e:
        return await event.reply(f'Error: {e}')

    sts = await event.reply("Generating link for your message.\nThis may take time depending on the number of messages.")
    me = await bot.get_me()
    U_NAME = f"{me.username}"
    string = f"{f_msg_id}_{l_msg_id}_{chat.id}_{cmd.lower().strip()}"
    b_64 = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    await sts.edit(f"Here is your link: https://t.me/{U_NAME}?start=DSTORE-{b_64}")


@bot.on(
    events.NewMessage(incoming=True, pattern="^/about", func=lambda e: e.is_private)
)
async def _(e):
    await admin._about(e)


@bot.on(events.callbackquery.CallbackQuery(data="slog"))
async def _(e):
    await admin._logs(e)


@bot.on(events.callbackquery.CallbackQuery(data="sret"))
async def _(e):
    await admin._restart(e, schedule)


@bot.on(events.callbackquery.CallbackQuery(data="entg"))
async def _(e):
    await admin._encode_t(e)


@bot.on(events.callbackquery.CallbackQuery(data="butg"))
async def _(e):
    await admin._btn_t(e)


@bot.on(events.callbackquery.CallbackQuery(data="scul"))
async def _(e):
    await admin._sep_c_t(e)


@bot.on(events.callbackquery.CallbackQuery(data="cast"))
async def _(e):
    await admin.broadcast_bt(e)


@bot.on(events.callbackquery.CallbackQuery(data="bek"))
async def _(e):
    await e.edit(buttons=admin.admin_panel())


async def anime(data):
    try:
        torr = [data.get("480p"), data.get("720p"), data.get("1080p")]
        anime_info = AnimeInfo(torr[0].title)
        poster = await tools._poster(bot, anime_info)
        if await dB.is_separate_channel_upload():
            chat_info = await tools.get_chat_info(bot, anime_info, dB)
            await poster.edit(
                buttons=[
                    [
                        Button.url(
                            f"EPISODE {anime_info.data.get('episode_number', '')}".strip(),
                            url=chat_info["invite_link"],
                        )
                    ]
                ]
            )
            poster = await tools._poster(bot, anime_info, chat_info["chat_id"])
        btn = [[]]
        original_upload = await dB.is_original_upload()
        button_upload = await dB.is_button_upload()
        for i in torr:
            try:
                filename = f"downloads/{i.title}"
                reporter = Reporter(bot, i.title)
                await reporter.alert_new_file_founded()
                await torrent.download_magnet(i.link, "./downloads/")
                exe = Executors(
                    bot,
                    dB,
                    {
                        "original_upload": original_upload,
                        "button_upload": button_upload,
                    },
                    filename,
                    AnimeInfo(i.title),
                    reporter,
                )
                result, _btn = await exe.execute()
                if result:
                    if _btn:
                        if len(btn[0]) == 2:
                            btn.append([_btn])
                        else:
                            btn[0].append(_btn)
                        await poster.edit(buttons=btn)
                    asyncio.ensure_future(exe.further_work())
                    continue
                await reporter.report_error(_btn, log=True)
                await reporter.msg.delete()
            except BaseException:
                await reporter.report_error(str(format_exc()), log=True)
                await reporter.msg.delete()
    except BaseException:
        LOGS.error(str(format_exc()))


try:
    delete_files()
    bot.loop.run_until_complete(subsplease.on_new_anime(anime))
    bot.run()
except KeyboardInterrupt:
    subsplease._exit()
