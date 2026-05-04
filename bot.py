import os
import asyncio
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify
import threading

# ========== التوكنات والمفاتيح ==========
TELEGRAM_TOKEN = "8743390722:AAHBb9LVRJHUmccEK-xGcc32YQw5rE_KAnY"
GEMINI_API_KEY = "AIzaSyCWDo3VlPLsTPs5b4zKNzHAmdSC8U29Rsw"  # 🔑 حط مفتاحك هنا

# ========== تشغيل Gemini ==========
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

# ========== الأيقونات ==========
I = {
    "doc": "👨‍⚕️", "emerg": "🚨", "hospital": "🏥", "diagnosis": "🔬",
    "treatment": "💊", "advice": "📝", "warning": "⚠️", "loc": "📍",
    "phone": "📞", "brain": "🧠", "steth": "🩺", "heart": "❤️"
}

# ========== معلومات المستشفى ==========
HOSPITAL = {
    "name": "مستشفى الجمهوري التعليمي - صنعاء",
    "address": "شارع إسماعيل هنية (الزبيري سابقاً)",
    "phone": "781695995",
    "complaints": "779157779",
}

# ========== دالة التحليل الطبي الذكي ==========
async def medical_analysis(symptoms):
    try:
        prompt = f"""أنت استشاري طبي في {HOSPITAL['name']}.

الأعراض: {symptoms}

رد بهذا التنسيق بالضبط مع الأيقونات:

{I['steth']} *الاستشارة الطبية*

{I['brain']} *تحليل الأعراض:*
[تحليل دقيق]

{I['diagnosis']} *التشخيص المبدئي:*
[احتمالان أو ثلاثة]

{I['treatment']} *العلاج والنصائح:*
• [نصيحة 1]
• [نصيحة 2]

{I['hospital']} *القسم المناسب:*
[اسم القسم]

{I['warning']} *هذا تشخيص أولي، استشر الطبيب المختص*

📞 للطوارئ: {HOSPITAL['phone']}"""
        
        response = model.generate_content(prompt)
        return response.text if response else None
    except Exception as e:
        return None

# ========== دوال البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(f"{I['steth']} استشارة طبية")],
        [KeyboardButton(f"{I['hospital']} معلومات المستشفى"), KeyboardButton(f"{I['emerg']} طوارئ")],
        [KeyboardButton(f"{I['phone']} أرقام التواصل"), KeyboardButton(f"{I['loc']} الموقع")]
    ]
    await update.message.reply_text(
        f"{I['hospital']} *{HOSPITAL['name']}*\n\n"
        f"{I['brain']} بوت طبي ذكي يقدم:\n"
        f"• تشخيص دقيق\n"
        f"• علاجات ونصائح\n"
        f"• توجيه للقسم المناسب\n\n"
        f"📞 الطوارئ: {HOSPITAL['phone']}\n\n"
        f"*اكتب أعراضك أو اضغط على الزر السفلي*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def hospital_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{I['hospital']} *{HOSPITAL['name']}*\n\n"
        f"{I['loc']} {HOSPITAL['address']}\n"
        f"{I['phone']} {HOSPITAL['phone']}\n"
        f"{I['phone']} للشكاوى: {HOSPITAL['complaints']}\n\n"
        f"الخدمات مجانية بالكامل",
        parse_mode="Markdown"
    )

async def emergency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{I['emerg']} *حالة طارئة* {I['emerg']}\n\n"
        f"اتصل فوراً:\n"
        f"📞 {HOSPITAL['phone']}\n"
        f"📍 {HOSPITAL['address']}\n\n"
        f"{I['warning']} لا تنتظر، اذهب لأقرب طوارئ",
        parse_mode="Markdown"
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{I['phone']} *أرقام التواصل*\n\n"
        f"للاستفسار: {HOSPITAL['phone']}\n"
        f"للشكاوى: {HOSPITAL['complaints']}",
        parse_mode="Markdown"
    )

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{I['loc']} *الموقع*\n\n{HOSPITAL['address']}\n\nوسط العاصمة صنعاء",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    if msg == f"{I['steth']} استشارة طبية":
        await update.message.reply_text(f"{I['steth']} اكتب أعراضك بالتفصيل وسأحللها لك...")
    elif msg == f"{I['hospital']} معلومات المستشفى":
        await hospital_info(update, context)
    elif msg == f"{I['emerg']} طوارئ":
        await emergency(update, context)
    elif msg == f"{I['phone']} أرقام التواصل":
        await contact(update, context)
    elif msg == f"{I['loc']} الموقع":
        await location(update, context)
    else:
        # استشارة طبية
        thinking = await update.message.reply_text(f"{I['brain']} جاري تحليل الأعراض和治疗...")
        
        response = await medical_analysis(msg)
        
        if response:
            await thinking.edit_text(response, parse_mode="Markdown")
        else:
            await thinking.edit_text(
                f"{I['warning']} عذراً، حدث خطأ. يرجى الاتصال على {HOSPITAL['phone']}\n\n"
                f"أو أعد كتابة الأعراض بشكل أوضح"
            )

# ========== إعداد Flask ==========
app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/')
def home():
    return jsonify({"status": "✅ البوت الطبي الذكي شغال", "bot": "@Hospitalalg_bot"})

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
    threading.Thread(target=run_flask).start()
    print("✅ البوت الطبي الذكي شغال...")
    telegram_app.run_polling()
