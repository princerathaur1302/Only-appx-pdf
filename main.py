from pyrogram import Client, filters
import requests
import os
import time
from urllib.parse import quote

API_ID = 20214595
API_HASH = "4763f66ce1a18c2dd491a5048891926c"
BOT_TOKEN = "8609058610:AAHaLZFKchOHOny6xGHQSBz7ZdOv0011pd8"
CREDIT = "@contact_262524_bot"

PDF_API = "https://studyuk.site/rwaapi/pdfdl.php?url="

app = Client(
    "pdf_only_batch_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

message_tracker = {}


# ================= MESSAGE TRACK =================
async def track_message(msg):
    chat_id = msg.chat.id
    message_tracker.setdefault(chat_id, []).append(msg.id)


async def delete_tracked_messages(client, chat_id):
    if chat_id in message_tracker:
        for msg_id in message_tracker[chat_id]:
            try:
                await client.delete_messages(chat_id, msg_id)
            except:
                pass
        message_tracker[chat_id] = []


# ================= DOWNLOAD PDF =================
async def download_pdf(url, dest_path, msg):
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()

    total = int(r.headers.get("content-length", 0))
    downloaded = 0
    start_time = time.time()
    last_update = 0

    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(1024 * 512):
            if not chunk:
                continue

            f.write(chunk)
            downloaded += len(chunk)

            now = time.time()
            if now - last_update >= 3:
                percent = (downloaded / total * 100) if total else 0
                speed = downloaded / max(now - start_time, 1) / (1024 * 1024)

                try:
                    await msg.edit(
                        f"📥 Downloading PDF...\n"
                        f"├ Progress: {percent:.2f}%\n"
                        f"├ Speed: {speed:.2f} MB/s\n"
                        f"└ {downloaded // (1024*1024)} MB"
                    )
                except:
                    pass
                last_update = now


# ================= UPLOAD PDF =================
async def upload_pdf(client, chat_id, file_path, caption):
    upload_msg = await client.send_message(chat_id, "📤 Uploading PDF...")
    await track_message(upload_msg)

    async def progress(current, total):
        percent = current * 100 / total
        try:
            await upload_msg.edit_text(f"📤 Uploading... {percent:.2f}%")
        except:
            pass

    await client.send_document(
        chat_id,
        file_path,
        caption=caption,
        progress=progress
    )

    try:
        await upload_msg.delete()
    except:
        pass

    if os.path.exists(file_path):
        os.remove(file_path)


# ================= COMMANDS =================
@app.on_message(filters.command("start"))
async def start(client, message):
    msg = await message.reply("👋 Use /batch and send TXT file")
    await track_message(msg)


@app.on_message(filters.command("batch"))
async def batch(client, message):
    msg = await message.reply("📄 Send TXT file now")
    await track_message(msg)


# ================= TXT HANDLER =================
@app.on_message(filters.document & filters.private)
async def handle_txt(client, message):
    if not message.document.file_name.endswith(".txt"):
        return

    chat_id = message.chat.id
    batch_name = os.path.splitext(message.document.file_name)[0]

    processing = await message.reply("📥 Processing TXT...")
    await track_message(processing)

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
            url = "https://" + url.strip()

            # ================= SKIP VIDEOS =================
            if "transcoded" in url.lower() or ".m3u8" in url.lower():
                print(f"⏭ Skipped video: {title}")
                continue

            # ================= PDF LOGIC =================
            if ".pdf" in url.lower():

                # Protected Appx PDF
                if "URLPrefix" in url:
                    final_url = PDF_API + quote(url, safe="")
                else:
                    final_url = url
            else:
                # Static hidden PDF
                final_url = PDF_API + quote(url, safe="")

            pdf_name = f"{title.replace('/', '_').replace(' ', '_')}.pdf"

            msg = await message.reply(f"📄 Downloading: {title}")
            await track_message(msg)

            try:
                await download_pdf(final_url, pdf_name, msg)

                caption = (
                    f"📄 **Title:** {title}\n"
                    f"📦 **Batch:** {batch_name}\n\n"
                    f"**Contact ➤** {CREDIT}"
                )

                await upload_pdf(client, chat_id, pdf_name, caption)

            except Exception as e:
                await msg.edit(f"❌ Failed: {title}\n{str(e)}")

        try:
            await processing.delete()
        except:
            pass

        if os.path.exists(txt_path):
            os.remove(txt_path)

    except Exception as e:
        await processing.edit(f"❌ Error: {str(e)}")


print("🔥 PDF BOT STARTED")
app.run()
