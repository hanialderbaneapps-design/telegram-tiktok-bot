import os
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@professionalXoX"  # اسم قناتك
# ====================

# Regex صحيح يقبل كل روابط تيك توك
TIKTOK_RE = re.compile(
    r"(https?://)?(www\.)?(tiktok\.com|vt\.tiktok\.com)/\S+",
    re.IGNORECASE
)

# تحقق من الاشتراك
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً 👋\nابعت رابط فيديو تيك توك وسأحمله لك بدون علامة مائية."
    )

# الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # تحقق الرابط
    if not TIKTOK_RE.search(text):
        await update.message.reply_text(
            "❌ ابعت رابط تيك توك صحيح\nمثال:\nhttps://vt.tiktok.com/..."
        )
        return

    # تحقق الاشتراك
    if not await is_subscribed(update.effective_user.id, context):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك بالقناة", url=f"https://t.me/{CHANNEL.lstrip('@')}")],
            [InlineKeyboardButton("✅ تحقق", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            "⚠️ يجب الاشتراك بالقناة أولاً",
            reply_markup=keyboard
        )
        return

    await update.message.reply_text("⏳ جاري تحميل الفيديو...")

    filename = f"video_{update.effective_user.id}.mp4"

    ydl_opts = {
        "outtmpl": filename,
        "format": "best",
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([text])

        await update.message.reply_video(
            video=open(filename, "rb"),
            caption="✅ تم التحميل بنجاح"
        )

    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ أثناء التحميل")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# تحقق الزر
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_subscribed(query.from_user.id, context):
        await query.edit_message_text("✅ أنت مشترك، ابعت رابط تيك توك الآن")
    else:
        await query.answer("❌ لم تشترك بعد", show_alert=True)

# main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(
        telegram.ext.CallbackQueryHandler(button, pattern="check_sub")
    )

    app.run_polling()

if __name__ == "__main__":
    main()
