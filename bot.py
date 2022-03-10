# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# 
# For more information, please refer to <https://unlicense.org>

# dependencies are telegram-python-bot, requests and yt-dlp; pip install them

import os
import inspect
import tempfile
import requests
import ffmpeg
from telegram import Update, ParseMode
from telegram.ext import Updater, CallbackContext, MessageHandler, CommandHandler, Filters
from yt_dlp import YoutubeDL

import logging; logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv('TELEGRAM')
if not TOKEN:
    raise Exception('Set TELEGRAM Environment variable to your telegram bot key')

updater = Updater(token=TOKEN)

def escape(inp: str) -> str:
    for a, b in {'&': '&amp;', '<': '&lt;', '>': '&gt;'}.items():
        inp = inp.replace(a, b)
    return inp

def on_message(update: Update, context: CallbackContext):
    tmps = [tempfile.mkstemp(suffix=".mp4")[1] for i in range(2)]
    with YoutubeDL({'silent': True, 'outtmpl': tmps[0], 'overwrites': True}) as ydl:
        url = update.message.text
        while any(filter in url for filter in ['vm.tiktok.com', 'm.tiktok.com']):
            url = requests.head(url).headers['Location']
        info_dict = ydl.sanitize_info(ydl.extract_info(url, download=False))
        if info_dict['extractor'] != "TikTok":
            return update.message.reply_text('Send an actual TikTok link.')
        ydl.extract_info(url)
        ffmpeg.input(tmps[0]).output(tmps[1], vcodec="libx264", loglevel="fatal", y=None).run()
        with open(tmps[1], mode='rb') as video:
            update.message.reply_video(video=video, parse_mode=ParseMode().HTML, caption=f"<pre>{escape(info_dict['title'])}</pre>\nby https://tiktok.com/@{escape(info_dict['uploader'])}\n<pre>{escape(info_dict['uploader'])}|{escape(info_dict['id'])}</pre>\nDownloaded with @{escape(context.bot.username)}")
        _ = [os.remove(tmp) for tmp in tmps]

def send_code(update: Update, context: CallbackContext):
    update.message.reply_document(open(inspect.getfile(lambda: None), 'rb'), filename='bot.py')

def start(update: Update, context: CallbackContext):
    update.message.reply_text(f'Hey, im @{escape(context.bot.username)}\nYou can use me to download TikTok videos\nYou can get my code with /code')

updater.dispatcher.add_handler(CommandHandler('start', start, run_async=True))
updater.dispatcher.add_handler(CommandHandler('code', send_code, run_async=True))
updater.dispatcher.add_handler(MessageHandler(Filters.text&(~Filters.command), on_message, run_async=True))

updater.start_polling()