import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import asyncio

# ========== إعدادات التسجيل ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== التوكنات والمفاتيح ==========
TELEGRAM_TOKEN = "8743390722:AAFT-L67uXzkipfd-C29-GOBGTHPolHFyX8"
GEMINI_API_KEY = "AIzaSyCWDo3VlPLsTPs5b4zKNzHAmdSC8U29Rsw"

# ========== تشغيل Gemini ==========
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ========== الأيقونات ==========
I = {
    "doc": "👨‍⚕️", "emerg": "🚨", "hospital": "🏥", "diagnosis": "🔬",
    "treatment": "💊", "advice": "📝", "warning": "⚠️", "loc": "📍",
    "phone": "📞", "brain": "🧠", "steth": "🩺", "heart": "❤️", 
    "success": "✅", "media": "📺", "facebook": "📘", "twitter": "🐦",
    "instagram": "📷", "youtube": "🎥", "whatsapp": "💬", "telegram": "✈️"
}

# ========== معلومات المستشفى ==========
HOSPITAL = {
    "name": "مستشفى الجمهوري التعليمي - صنعاء",
    "address": "شارع إسماعيل هنية (الزبيري سابقاً) - أمانة العاصمة",
    "phone": "781695995",
    "complaints": "779157779",
    "email": "info@algumhorihosp-san.gov.ye",
    "whatsapp": "http://wa.me/967734734696",
    "beds": "650 سرير",
}

# ========== روابط التواصل الاجتماعي ==========
SOCIAL_MEDIA = {
    "telegram": "https://t.me/ALGUMHORI",
    "facebook_main": "https://www.facebook.com/GHTSMS",
    "facebook_interactive": "https://www.facebook.com/algumhori",
    "facebook_media": "https://www.facebook.com/GHT734734696",
    "x": "https://x.com/GHTSMS",
    "instagram": "https://instagram.com/algumhori.ye",
    "youtube": "https://youtube.com/@algumhori_live_ye",
    "threads": "https://www.threads.net/@algumhori.ye",
    "whatsapp_direct": "http://wa.me/967734734696"
}

# ========== الأقسام الطبية ==========
DEPARTMENTS = ["الباطنية", "الجراحة العامة", "العظام والمفاصل", "الأطفال", "الطوارئ", "العيون", "الجلدية", "المسالك البولية", "الأنف والأذن والحنجرة"]

# ========== الكوادر الطبية ==========
DOCTORS = {
    "رئيس الهيئة": "أ.د. محمد طاهر جحاف",
    "نائب رئيس الهيئة": "د. عمار قداري",
    "رئيس قسم العظام": "د/معتز الصنوي",
    "رئيس قسم الجراحة": "د/عبدالله الاشول",
    "رئيس قسم الباطنية": "د/عبد الواسع مجاهد",
}

# ========== دالة التحليل الطبي الذكي ==========
async def medical_analysis(symptoms):
    """تحليل الأعراض وتقديم استشارة طبية"""
    try:
        prompt = f"""أنت استشاري طبي في {HOSPITAL['name']}. الأعراض: {symptoms}

رد بهذا التنسيق بالضبط مع الأيقونات:

{I['steth']} *الاستشارة الطبية*

{I['brain']} *تحليل الأعراض:*
[اكتب تحليلاً دقيقاً للأعراض]

{I['diagnosis']} *التشخيص المبدئي:*
• [الاحتمال الأول]
• [الاحتمال الثاني]

{I['treatment']} *العلاج والنصائح:*
• [نصيحة 1]
• [نصيحة 2]

{I['hospital']} *القسم المناسب:*
[اسم القسم من: {', '.join(DEPARTMENTS)}]

{I['warning']} *هذا تشخيص أولي، استشر الطبيب المختص*

📞 للطوارئ: {HOSPITAL['phone']}"""
        
        response = model.generate_content(prompt)
        return response.text if response else None
    except Exception as e:
        logger.error(f"خطأ في Gemini: {e}")
        return None

# ========== دوال البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(f"{I['steth']} استشارة طبية")],
        [KeyboardButton(f"{I['hospital']} المستشفى"), KeyboardButton(f"{I['doc']} الكوادر")],
        [KeyboardButton(f"{I['emerg']} طوارئ"), KeyboardButton(f"{I['phone']} التواصل")],
        [KeyboardButton(f"{I['loc']} الموقع"), KeyboardButton(f"{I['heart']} الأقسام")],
        [KeyboardButton(f"{I['media']} المركز الإعلامي"), KeyboardButton(f"{I['whatsapp']} واتساب مباشر")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"{I['hospital']} *{HOSPITAL['name']}*\n\n"
        f"{I['brain']} *بوت طبي ذكي بالذكاء الاصطناعي*\n\n"
        f"{I['success']} أقدم لك:\n"
        f"• تحليل دقيق للأعراض\n"
        f"• تشخيص مبدئي\n"
        f"• علاجات ونصائح\n"
        f"• توجيه للقسم المناسب\n\n"
        f"{I['media']} تابع المركز الإعلامي على وسائل التواصل\n\n"
        f"{I['emerg']} *للطوارئ:* {HOSPITAL['phone']}\n\n"
        f"*اكتب أعراضك أو اختر من القائمة*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def hospital_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{I['hospital']} *{HOSPITAL['name']}*

{I['loc']} {HOSPITAL['address']}
{I['phone']} {HOSPITAL['phone']}
{I['phone']} للشكاوى: {HOSPITAL['complaints']}
{I['heart']} السعة: {HOSPITAL['beds']} سرير

*الخدمات:* مجانية بالكامل
*الطوارئ:* 24 ساعة"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def doctors_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    docs = "\n".join([f"• *{title}:* {name}" for title, name in DOCTORS.items()])
    text = f"{I['doc']} *الكوادر الطبية الرئيسية*\n\n{docs}\n\n📞 للاستفسار: {HOSPITAL['phone']}"
    await update.message.reply_text(text, parse_mode="Markdown")

async def emergency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{I['emerg']} *حالة طارئه* {I['emerg']}

*اتصل فوراً:*
📞 {HOSPITAL['phone']}
📍 {HOSPITAL['address']}

{I['warning']} لا تنتظر، اذهب لأقرب طوارئ"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{I['phone']} *أرقام التواصل*

للاستفسار: {HOSPITAL['phone']}
للشكاوى: {HOSPITAL['complaints']}
📧 {HOSPITAL['email']}"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"{I['loc']} *الموقع*\n\n{HOSPITAL['address']}\n\nوسط العاصمة صنعاء - يسهل الوصول إليه"
    await update.message.reply_text(text, parse_mode="Markdown")

async def departments_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    depts = "\n".join([f"• {dept}" for dept in DEPARTMENTS])
    text = f"{I['hospital']} *الأقسام الطبية*\n\n{depts}"
    await update.message.reply_text(text, parse_mode="Markdown")

async def consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{I['steth']} *استشارة طبية فورية*\n\n"
        f"اكتب أعراضك بالتفصيل (متى بدأت، شدتها، مكانها)\n\n"
        f"📝 *مثال:* 'عندي ألم في الصدر من 3 أيام، يزداد مع الحركة'\n\n"
        f"{I['brain']} سأقوم بتحليلها وتقديم استشارة لك",
        parse_mode="Markdown"
    )

async def media_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المركز الإعلامي - روابط التواصل الاجتماعي"""
    text = f"""{I['media']} *المركز الإعلامي - هيئة المستشفى الجمهوري التعليمي* {I['media']}

تابعونا على جميع وسائل التواصل الاجتماعي:

{I['telegram']} *تلغرام:* [ALGUMHORI]({SOCIAL_MEDIA['telegram']})

{I['facebook']} *فيسبوك - الأخبار الرئيسية:* [GHTSMS]({SOCIAL_MEDIA['facebook_main']})
{I['facebook']} *فيسبوك - الأخبار التفاعلية:* [algumhori]({SOCIAL_MEDIA['facebook_interactive']})
{I['facebook']} *فيسبوك - المركز الإعلامي:* [GHT734734696]({SOCIAL_MEDIA['facebook_media']})

{I['twitter']} *إكس (تويتر):* [@GHTSMS]({SOCIAL_MEDIA['x']})

{I['instagram']} *انستجرام:* [algumhori.ye]({SOCIAL_MEDIA['instagram']})

{I['youtube']} *يوتيوب:* [algumhori_live_ye]({SOCIAL_MEDIA['youtube']})

{I['media']} *ثريدز:* [algumhori.ye]({SOCIAL_MEDIA['threads']})

💬 *واتساب مباشر:* [اضغط هنا للتواصل]({SOCIAL_MEDIA['whatsapp_direct']})

---
📞 للطوارئ: {HOSPITAL['phone']}
📍 {HOSPITAL['address']}"""
    
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)

async def whatsapp_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """واتساب مباشر"""
    text = f"""{I['whatsapp']} *تواصل مباشر عبر الواتساب* {I['whatsapp']}

اضغط على الرابط أدناه للتواصل المباشر مع فريق المستشفى عبر الواتساب:

📱 [تواصل الآن عبر الواتساب]({SOCIAL_MEDIA['whatsapp_direct']})

يمكنك استخدام هذه الخدمة لـ:
• حجز المواعيد
• الاستفسار عن الخدمات
• تقديم الملاحظات والاقتراحات

📞 أو اتصل على: {HOSPITAL['phone']}"""
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    # معالجة الأزرار
    if msg == f"{I['steth']} استشارة طبية":
        await consultation(update, context)
    elif msg == f"{I['hospital']} المستشفى":
        await hospital_info(update, context)
    elif msg == f"{I['doc']} الكوادر":
        await doctors_info(update, context)
    elif msg == f"{I['emerg']} طوارئ":
        await emergency(update, context)
    elif msg == f"{I['phone']} التواصل":
        await contact(update, context)
    elif msg == f"{I['loc']} الموقع":
        await location(update, context)
    elif msg == f"{I['heart']} الأقسام":
        await departments_info(update, context)
    elif msg == f"{I['media']} المركز الإعلامي":
        await media_center(update, context)
    elif msg == f"{I['whatsapp']} واتساب مباشر":
        await whatsapp_direct(update, context)
    else:
        # استشارة طبية ذكية
        thinking = await update.message.reply_text(f"{I['brain']} جاري تحليل الأعراض وتجهيز الاستشارة...")
        
        response = await medical_analysis(msg)
        
        if response:
            await thinking.edit_text(response, parse_mode="Markdown")
        else:
            await thinking.edit_text(
                f"{I['warning']} *عذراً، حدث خطأ تقني*\n\n"
                f"الرجاء المحاولة مرة أخرى أو الاتصال على:\n"
                f"📞 {HOSPITAL['phone']}\n\n"
                f"أعد كتابة الأعراض بشكل أوضح",
                parse_mode="Markdown"
            )

# ========== إعداد Flask و Webhook ==========
app = Flask(__name__)

# إنشاء تطبيق Telegram
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# إضافة المعالجات
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/')
def home():
    return jsonify({
        "status": "✅ البوت الطبي الذكي شغال",
        "bot": "@Hospitalalg_bot",
        "version": "Golden Edition with Media Center",
        "ai": "Gemini 1.5 Flash"
    })

@app.route('/webhook', methods=['POST'])
async def webhook():
    """استقبال التحديثات من Telegram"""
    try:
        update_data = request.get_json()
        if update_data:
            update = Update.de_json(update_data, telegram_app.bot)
            await telegram_app.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"خطأ في webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# ========== التشغيل ==========
if __name__ == '__main__':
    # تعيين webhook
    webhook_url = "https://hospital-bot.onrender.com/webhook"
    
    logger.info(f"🚀 تشغيل البوت الطبي الذكي...")
    logger.info(f"📍 Webhook URL: {webhook_url}")
    
    # تشغيل Flask
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
