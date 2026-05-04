import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify
import threading

# ================= التوكن =================
TOKEN = "8743390722:AAHLDi36JpRC5AJabXPTA6yzERK6MdVTo6c"

# ================= معلومات المستشفى =================
HOSPITAL_INFO = {
    "name": "مستشفى الجمهوري التعليمي - صنعاء",
    "phone": "781695995",
    "address": "شارع إسماعيل هنية (الزبيري سابقاً) - أمانة العاصمة"
}

# ================= دوال البوت =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏥 *{HOSPITAL_INFO['name']}*\n\n"
        f"مرحباً بك! أرسل أي استفسار طبي وسأساعدك.\n"
        f"📞 للطوارئ: {HOSPITAL_INFO['phone']}",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    if "طوارئ" in user_message:
        reply = f"🚨 حالة طارئة! اتصل فوراً على {HOSPITAL_INFO['phone']}"
    elif "شكرا" in user_message:
        reply = "على الرحب والسعة! 🌹"
    else:
        reply = f"📞 للاستفسار، يرجى الاتصال على {HOSPITAL_INFO['phone']}"
    await update.message.reply_text(reply)

# ================= إعداد Flask لـ Render =================
app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/')
def home():
    return jsonify({"status": "✅ البوت شغال"})

@app.route('/webhook', methods=['POST'])
async def webhook():
    update_data = request.get_json()
    if update_data:
        update = Update.de_json(update_data, telegram_app.bot)
        await telegram_app.process_update(update)
    return jsonify({"status": "ok"}), 200

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == '__main__':
    # تشغيل Flask في الخلفية
    threading.Thread(target=run_flask).start()
    # تشغيل Polling (للتشغيل المباشر)
    print("✅ البوت يعمل...")
    telegram_app.run_polling()
