import os
import re
import tempfile
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@professionalXoX"  # t.me/professionalXoX

TIKTOK_RE = re.compile(r"(https?://)?(www\.)?(tiktok\.com|vt\.tiktok\.com)/\S+", re.IGNORECASE)

def join_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("اشترك بالقناة أولاً", url=f"https://t.me/{CHANNEL.lstrip('@')}")]
    ])

async def is_subscribed(bot, user_id: int) -> bool:
    try:
        m = await bot.get_chat_member(CHANNEL, user_id)
        return m.status in ("member", "administrator", "creator")
    except Exception:
        return False

def extract_tiktok_url(text: str) -> str | None:
    m = TIKTOK_RE.search(text or "")
    return m.group(0) if m else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أرسل رابط تيك توك هنا.\n"
        "إذا لم تكن مشتركاً بالقناة، سيطلب منك الاشتراك تلقائياً.",
        reply_markup=join_kb()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 1) تحقق لحظي من الاشتراك (كل مرة)
    if not await is_subscribed(context.bot, user_id):
        await update.message.reply_text(
            "آسف، لازم تشترك بالقناة أولاً ثم أرسل الرابط المراد تحميله.",
            reply_markup=join_kb()
        )
        return

    # 2) استخرج رابط تيك توك
    url = extract_tiktok_url(update.message.text or "")
    if not url:
        await update.message.reply_text("ابعت رابط تيك توك صحيح (مثال: https://vt.tiktok.com/...)")
        return

    status_msg = await update.message.reply_text("تمام… جاري التحميل ⏳")

    # 3) تنزيل وإرسال (كما يتيحه المصدر)
    with tempfile.TemporaryDirectory() as td:
        outtmpl = os.path.join(td, "video.%(ext)s")
        cmd = ["yt-dlp", "-o", outtmpl, "-f", "bv*+ba/best", "--no-playlist", url]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            await status_msg.edit_text("صار خطأ بالتحميل. ممكن الرابط خاص/محمي أو المصدر مانع التنزيل.")
            return

        files = [os.path.join(td, f) for f in os.listdir(td) if f.startswith("video.")]
        if not files:
            await status_msg.edit_text("تم التحميل لكن لم أجد الملف الناتج.")
            return

        video_path = files[0]
        try:
            await status_msg.edit_text("جاري الإرسال ✅")
            with open(video_path, "rb") as f:
                await update.message.reply_document(document=f, filename="tiktok.mp4")
        except Exception:
            await status_msg.edit_text("ما قدرت أرسل الملف (ممكن حجمه كبير). جرّب فيديو أقصر.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
