import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
import asyncio

# ========== إعدادات التسجيل ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== التوكنات (ضع مفاتيحك هنا) ==========
TELEGRAM_TOKEN = "8743390722:AAFT-L67uXzkipfd-C29-GOBGTHPolHFyX8"
GEMINI_API_KEY = "AIzaSyCWDo3VlPLsTPs5b4zKNzHAmdSC8U29Rsw"

# ========== تشغيل Gemini ==========
client = genai.Client(api_key=GEMINI_API_KEY)

# ========== الأيقونات ==========
I = {
    "doc": "👨‍⚕️", "emerg": "🚨", "hospital": "🏥", "diagnosis": "🔬",
    "treatment": "💊", "advice": "📝", "warning": "⚠️", "loc": "📍",
    "phone": "📞", "brain": "🧠", "steth": "🩺", "heart": "❤️", 
    "success": "✅", "media": "📺", "info": "ℹ️", "faq": "❓",
    "link": "🔗", "whatsapp": "💬"
}

# ========== قاعدة البيانات المحدثة ==========
HOSPITAL = {
    "name": "هيئة المستشفى الجمهوري التعليمي - صنعاء",
    "description": "أحد أقدم وأكبر المستشفيات الحكومية، يقدم خدمات طبية مجانية بسعة تتجاوز 500 سرير.",
    "address": "شارع الزبيري (إسماعيل هنية حالياً) - أمانة العاصمة",
    "phone": "781695995",
    "complaints": "779157779",
    "email": "info@algumhorihosp-san.gov.ye",
    "beds": "500+ سرير",
}

DOCTORS = {
    "رئيس الهيئة": "أ.د. محمد طاهر جحاف (استشاري عظام ومفاصل)",
    "نائب الشؤون الفنية": "د. عمار قداري",
    "نائب الشؤون السريرية": "د. نبيل الحاج",
    "نائب الشؤون الأكاديمية": "أ.د. محمد البعداني",
}

DEPARTMENTS = [
    "الجراحة العامة", "العظام", "الباطنية", "الأطفال والحضانة", 
    "العناية المركزة", "الأنف والأذن والحنجرة", "الأمراض الجلدية",
    "جراحة المخ والأعصاب", "جراحة المسالك البولية", "جراحة الوجه والفكين"
]

CENTERS = [
    "مركز الحروق والتجميل", "مركز الكبد والجهاز الهضمي", "مركز العيون",
    "مركز الأمومة والطفولة", "مركز الغسيل الكلوي", "مركز الحميات", "مركز الطوارئ العامة"
]

# ========== دالة التحليل الطبي الذكي ==========
async def medical_analysis(user_query):
    try:
        # تعليمات النظام لضبط شخصية الذكاء الاصطناعي
        system_instruction = f"""
        أنت المساعد الذكي الرسمي لـ {HOSPITAL['name']}.
        معلومات المستشفى: {HOSPITAL['description']}.
        الموقع: {HOSPITAL['address']}.
        رئيس الهيئة: {DOCTORS['رئيس الهيئة']}.
        الأقسام المتوفرة: {', '.join(DEPARTMENTS)}.
        المراكز المتخصصة: {', '.join(CENTERS)}.
        
        قواعد الرد:
        1. إذا سأل المستخدم عن أعراض مرضية، قدم تحليلاً مبدئياً مهنياً مع التنبيه أنه ليس بديلاً عن الطبيب.
        2. وجه المريض دائماً للقسم أو المركز المناسب المتوفر لدينا في المستشفى.
        3. استخدم الأيقونات الطبية لجعل الرد مريحاً للقراءة.
        4. أجب باللغة العربية الفصحى.
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            config={'system_instruction': system_instruction},
            contents=user_query
        )
        return response.text if response else None
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return None

# ========== دوال البوت (Handlers) ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(f"{I['steth']} استشارة طبية ذكية")],
        [KeyboardButton(f"{I['hospital']} عن المستشفى"), KeyboardButton(f"{I['doc']} الإدارة")],
        [KeyboardButton(f"{I['heart']} الأقسام"), KeyboardButton(f"{I['diagnosis']} المراكز")],
        [KeyboardButton(f"{I['faq']} الأسئلة الشائعة"), KeyboardButton(f"{I['media']} المركز الإعلامي")],
        [KeyboardButton(f"{I['emerg']} الطوارئ"), KeyboardButton(f"{I['phone']} اتصل بنا")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = (
        f"{I['hospital']} *مرحباً بكم في {HOSPITAL['name']}*\n\n"
        f"أنا مساعدك الذكي، يمكنني مساعدتك في:\n"
        f"• تحليل الأعراض وتوجيهك للقسم المختص.\n"
        f"• تقديم معلومات عن الأطباء والإدارة.\n"
        f"• الإجابة على الأسئلة الشائعة حول خدماتنا المجانية.\n\n"
        f"*اكتب ما تشعر به أو اختر من القائمة أدناه:*"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def faq_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faq_text = (
        f"{I['faq']} *الأسئلة الشائعة*\n\n"
        f"*س: هل الخدمات مجانية؟*\n"
        f"ج: نعم، يقدم المستشفى خدماته بشكل مجاني في معظم الأقسام.\n\n"
        f"*س: هل توجد عيادات خارجية؟*\n"
        f"ج: نعم، يوجد قسم عيادات خارجية متكامل يعمل يومياً.\n\n"
        f"*س: أين يقع المستشفى؟*\n"
        f"ج: {HOSPITAL['address']}."
    )
    await update.message.reply_text(faq_text, parse_mode="Markdown")

async def hospital_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{I['hospital']} *{HOSPITAL['name']}*\n\n"
        f"{HOSPITAL['description']}\n\n"
        f"{I['loc']} الموقع: {HOSPITAL['address']}\n"
        f"{I['heart']} السعة: {HOSPITAL['beds']}\n"
        f"{I['success']} الخدمات: مجانية بالكامل للجمهور."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def leadership_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{I['doc']} *قيادة الهيئة*\n\n"
        f"• *رئيس الهيئة:* {DOCTORS['رئيس الهيئة']}\n"
        f"• *نائب (فني):* {DOCTORS['نائب الشؤون الفنية']}\n"
        f"• *نائب (سريري):* {DOCTORS['نائب الشؤون السريرية']}\n"
        f"• *نائب (أكاديمي):* {DOCTORS['نائب الشؤون الأكاديمية']}\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def depts_and_centers(update: Update, context: ContextTypes.DEFAULT_TYPE, mode="depts"):
    if mode == "depts":
        items = "\n".join([f"• {d}" for d in DEPARTMENTS])
        title = f"{I['heart']} الأقسام الطبية"
    else:
        items = "\n".join([f"• {c}" for c in CENTERS])
        title = f"{I['diagnosis']} المراكز المتخصصة"
    
    await update.message.reply_text(f"*{title}*\n\n{items}", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    if msg == f"{I['hospital']} عن المستشفى":
        await hospital_info(update, context)
    elif msg == f"{I['doc']} الإدارة":
        await leadership_info(update, context)
    elif msg == f"{I['heart']} الأقسام":
        await depts_and_centers(update, context, "depts")
    elif msg == f"{I['diagnosis']} المراكز":
        await depts_and_centers(update, context, "centers")
    elif msg == f"{I['faq']} الأسئلة الشائعة":
        await faq_info(update, context)
    elif msg == f"{I['phone']} اتصل بنا":
        await update.message.reply_text(f"{I['phone']} هاتف: {HOSPITAL['phone']}\n📧 {HOSPITAL['email']}")
    elif msg == f"{I['emerg']} الطوارئ":
        await update.message.reply_text(f"{I['emerg']} *طوارئ المستشفى تعمل 24 ساعة*\nاتصل فوراً: {HOSPITAL['phone']}")
    else:
        # معالجة الذكاء الاصطناعي
        thinking_msg = await update.message.reply_text(f"{I['brain']} جاري المعالجة...")
        ai_response = await medical_analysis(msg)
        if ai_response:
            await thinking_msg.edit_text(ai_response, parse_mode="Markdown")
        else:
            await thinking_msg.edit_text("عذراً، واجهت مشكلة في الاتصال بالذكاء الاصطناعي. حاول مرة أخرى.")

# ========== إعداد السيرفر (Flask) ==========
app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok", 200

if __name__ == '__main__':
    # للتشغيل المحلي استخدم Polling أو Webhook للاستضافة
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
