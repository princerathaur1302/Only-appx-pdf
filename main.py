from pyrogram import Client, filters
import requests
import os
import time
import re
from urllib.parse import quote

API_ID = 20214595
API_HASH = "4763f66ce1a18c2dd491a5048891926c"
BOT_TOKEN = "8609058610:AAHaLZFKchOHOny6xGHQSBz7ZdOv0011pd8"
CREDIT = "@contact_262524_bot"


PDF_API = "https://studyuk.site/rwaapi/pdfdl.php?url="

app = Client(
    "clean_pdf_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= DOWNLOAD =================
async def download_pdf(url, file_name, msg):
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()

    total = int(r.headers.get("content-length", 0))
    downloaded = 0
    start = time.time()
    last = 0

    with open(file_name, "wb") as f:
        for chunk in r.iter_content(1024 * 512):
            if not chunk:
                continue

            f.write(chunk)
            downloaded += len(chunk)

            now = time.time()
            if now - last >= 3:
                percent = (downloaded / total * 100) if total else 0
                speed = downloaded / max(now - start, 1) / (1024 * 1024)

                try:
                    await msg.edit(
                        f"📥 Downloading...\n"
                        f"{percent:.2f}% | {speed:.2f} MB/s"
                    )
                except:
                    pass
                last = now


# ================= UPLOAD =================
async def upload_pdf(client, chat_id, file_name, caption):
    msg = await client.send_message(chat_id, "📤 Uploading...")

    async def progress(current, total):
        percent = current * 100 / total
        try:
            await msg.edit(f"📤 Uploading {percent:.2f}%")
        except:
            pass

    await client.send_document(
        chat_id,
        file_name,
        caption=caption,
        progress=progress
    )

    try:
        await msg.delete()
    except:
        pass

    if os.path.exists(file_name):
        os.remove(file_name)


# ================= COMMAND =================
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("👋 Send TXT file with links")


# ================= TXT HANDLER =================
@app.on_message(filters.document & filters.private)
async def handle_txt(client, message):

    if not message.document.file_name.endswith(".txt"):
        return

    processing = await message.reply("📥 Processing...")

    txt_path = await message.download()

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()

            if ":https://" not in line:
                continue

            title, url = line.split(":https://", 1)
            title = title.strip()

            # ✅ REMOVE (Course Name)
            title = re.sub(r'^\(.*?\)\s*', '', title)

            url = "https://" + url.strip()

            # ❌ SKIP VIDEOS
            if "transcoded" in url.lower() or ".m3u8" in url.lower():
                print(f"⏭ Skipped video: {title}")
                continue

            # ✅ PDF LOGIC
            if ".pdf" in url.lower():
                if "URLPrefix" in url:
                    final_url = PDF_API + quote(url, safe="")
                else:
                    final_url = url
            else:
                final_url = PDF_API + quote(url, safe="")

            # ✅ CLEAN FILE NAME
            file_name = re.sub(r'[\\/:*?"<>|]', '_', title) + ".pdf"

            msg = await message.reply(f"📄 {title}")

            try:
                await download_pdf(final_url, file_name, msg)

                caption = f"📄 {title}"

                await upload_pdf(client, message.chat.id, file_name, caption)

            except Exception as e:
                await msg.edit(f"❌ Failed\n{str(e)}")

        try:
            await processing.delete()
        except:
            pass

        if os.path.exists(txt_path):
            os.remove(txt_path)

    except Exception as e:
        await processing.edit(f"❌ Error\n{str(e)}")
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_keepalive():
    server = HTTPServer(('0.0.0.0', 10000), KeepAliveHandler)
    server.serve_forever()

threading.Thread(target=run_keepalive).start()

print("🔥 Clean PDF Bot Started")
app.run()
