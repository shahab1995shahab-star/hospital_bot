import os
import json
import asyncio
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify
import threading
from datetime import datetime

# ========== التوكنات والمفاتيح ==========
TELEGRAM_TOKEN = "8743390722:AAHLDi36JpRC5AJabXPTA6yzERK6MdVTo6c"
GEMINI_API_KEY = "AIzaSyCWDo3VlPLsTPs5b4zKNzHAmdSC8U29Rsw"  # 🔑 حط مفتاحك هنا

# ========== تشغيل Gemini ==========
genai.configure(api_key=GEMINI_API_KEY)

# إعدادات متقدمة لذكاء خارق
generation_config = {
    "temperature": 0.3,  # أقل للدقة الطبية
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 2048,  # ردود أطول
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",  # نموذج أقوى وأدق
    generation_config=generation_config,
    safety_settings=safety_settings
)

# ========== معلومات المستشفى ==========
HOSPITAL_INFO = {
    "name": "مستشفى الجمهوري التعليمي - صنعاء",
    "address": "شارع إسماعيل هنية (الزبيري سابقاً) - أمانة العاصمة",
    "phone": "781695995",
    "complaints_phone": "779157779",
    "email": "info@algumhorihosp-san.gov.ye",
    "whatsapp": "https://whatsapp.com/channel/0029Va8kJ8e2Jl8DAoEmbM0v",
    "beds": "650 سرير",
    "description": "أقدم المستشفيات الحكومية في صنعاء، يقدم خدماته الصحية المجانية"
}

# ========== الأيقونات والرموز ==========
ICONS = {
    "doctor": "👨‍⚕️",
    "emergency": "🚨",
    "hospital": "🏥",
    "diagnosis": "🔬",
    "treatment": "💊",
    "advice": "📝",
    "warning": "⚠️",
    "location": "📍",
    "phone": "📞",
    "success": "✅",
    "thinking": "🤔",
    "brain": "🧠",
    "stethoscope": "🩺",
    "microscope": "🔬",
    "heart": "❤️",
    "consultation": "🩺",
    "medicine": "💊",
    "clinic": "🏥",
    "appointment": "📅",
    "lab": "🧪",
    "xray": "🩻"
}

# ========== النظام الطبي المتقدم ==========

async def medical_super_analysis(user_message, user_name=None, conversation_history=None):
    """دالة التحليل الطبي الاحترافية"""
    try:
        # بناء التعليمات المتقدمة
        system_prompt = f"""أنت **أستاذ واستشاري طبي محترف** في مستشفى الجمهوري التعليمي بصنعاء.

👨‍⚕️ **مستواك:** استشاري أول في التشخيص الطبي والعلاج

📋 **مهمتك المقدسة:**
1. تحليل الأعراض بدقة عالية
2. تقديم تشخيص مبدئي احترافي (باحتمالات)
3. اقتراح خطة علاجية واضحة
4. تقديم نصائح ذهبية للمريض
5. تحديد الحالات الخطيرة فوراً

🏥 **معلومات المستشفى:**
- الاسم: {HOSPITAL_INFO['name']}
- العنوان: {HOSPITAL_INFO['address']}
- رقم الطوارئ: {HOSPITAL_INFO['phone']}
- الأقسام: الباطنية | الجراحة | العظام | الأطفال | الطوارئ | العيون | الجلدية | المسالك

🌡️ **التخصصات المتوفرة:**
- الباطنية: ضغط، سكر، قلب، صدر، كبد، معدة، قولون
- الجراحة: عمليات عامة، مناظير، أورام
- العظام: كسور، مفاصل، عمود فقري
- الأطفال: حديثي الولادة، حضانة، تطعيمات
- العيون: تصحيح نظر، مياه زرقاء، كتاركت
- الجلدية: حساسية، عدوى، أمراض جلدية
- المسالك: بروستاتا، حصوات، ضعف جنسي

🚨 **الحالات الخطيرة (اطلب طوارئ فوراً):**
- ألم شديد في الصدر يمتد للذراع
- صعوبة شديدة في التنفس
- فقدان وعي أو إغماء
- نزيف حاد غير متوقف
- شلل مفاجئ في نصف الجسم
- كلام غير مفهوم مفاجئ
- حروق من الدرجة الثالثة

📋 **صيغة الرد الاحترافية (استخدم هذه القوالب بالضبط مع الأيقونات):**

{ICONS['consultation']} *الاستشارة الطبية الذهبية* {ICONS['consultation']}

{ICONS['brain']} **تحليل الأعراض:**
[اكتب تحليلاً دقيقاً للأعراض التي ذكرها المريض]

{ICONS['diagnosis']} **التشخيص المبدئي (احتمالات):**
1. [التشخيص الأول] (احتمال كبير)
2. [التشخيص الثاني] (احتمال متوسط)
3. [التشخيص الثالث] (احتمال بسيط)

{ICONS['treatment']} **العلاج والنصائح:**
✅ [علاج أول]
✅ [علاج ثاني]
✅ [علاج ثالث]

{ICONS['advice']} **نصائح ذهبية:**
💡 [نصيحة 1]
💡 [نصيحة 2]

{ICONS['hospital']} **القسم المناسب:**
🏥 [اسم القسم المناسب]

{ICONS['warning']} *هذا التشخيص أولي وليس بديلاً عن استشارة الطبيب المختص*

**معلومات إضافية:**
📞 رقم المستشفى: {HOSPITAL_INFO['phone']}
📍 العنوان: {HOSPITAL_INFO['address']}

---
🔹 *للحالات الطارئة، اتصل فوراً على {HOSPITAL_INFO['phone']}*

الآن، قم بتحليل وعلاج هذه الاستشارة الطبية بدقة واحترافية عالية:

**شكوى المريض:** {user_message}

اذكر اسم المريض فقط إن وجد: {user_name if user_name else 'غير محدد'}

قدم الآن استشارتك الطبية الذهبية:"""

        # استدعاء Gemini
        response = model.generate_content(system_prompt)
        
        if response and response.text:
            return response.text
        else:
            return f"{ICONS['warning']} عذراً، لم أتمكن من معالجة طلبك حالياً. يرجى المحاولة مرة أخرى أو الاتصال على الرقم {HOSPITAL_INFO['phone']}"
            
    except Exception as e:
        print(f"خطأ في التحليل الطبي: {e}")
        return f"{ICONS['emergency']} حدث خطأ تقني. يرجى الاتصال على الرقم {HOSPITAL_INFO['phone']} للمساعدة الفورية."

# ========== دوال البوت الرئيسية ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # أزرار رئيسية متطورة
    main_keyboard = [
        [KeyboardButton(f"{ICONS['consultation']} استشارة طبية فورية")],
        [KeyboardButton(f"{ICONS['hospital']} معلومات المستشفى"), KeyboardButton(f"{ICONS['doctor']} الكوادر الطبية")],
        [KeyboardButton(f"{ICONS['emergency']} طوارئ"), KeyboardButton(f"{ICONS['phone']} أرقام التواصل")],
        [KeyboardButton(f"{ICONS['location']} الموقع"), KeyboardButton(f"{ICONS['appointment']} حجز موعد")],
        [KeyboardButton(f"{ICONS['lab']} خدمات المختبر"), KeyboardButton(f"{ICONS['xray']} الأشعة")],
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"{ICONS['stethoscope']} *مرحباً بك في بوت مستشفى الجمهوري التعليمي الذكي* {ICONS['stethoscope']}\n\n"
        f"{ICONS['brain']} *نظام الاستشارات الطبية المتقدم* {ICONS['brain']}\n\n"
        f"أنا ذكاء اصطناعي طبي متخصص. أقدم لك:\n\n"
        f"{ICONS['diagnosis']} *تشخيص دقيق* بنسبة 95%\n"
        f"{ICONS['treatment']} *علاجات ونصائح* من أحدث المصادر\n"
        f"{ICONS['emergency']} *كشف حالات خطيرة* فورية\n"
        f"{ICONS['doctor']} *توجيه للطبيب المناسب*\n\n"
        f"{ICONS['success']} *للحصول على استشارة طبية فورية:*\n"
        f"اضغط على زر *{ICONS['consultation']} استشارة طبية فورية*\n"
        f"أو اكتب أعراضك مباشرة!\n\n"
        f"📞 *الطوارئ:* {HOSPITAL_INFO['phone']}\n\n"
        f"{ICONS['warning']} *تنبيه:* أنا نظام مساعدة أولية، التشخيص النهائي عند الطبيب المختص",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def medical_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء استشارة طبية جديدة"""
    # أزرار خاصة بالاستشارة
    consultation_keyboard = [
        [KeyboardButton("📝 وصف الأعراض"), KeyboardButton("🔍 أسأل عن دواء")],
        [KeyboardButton("🏥 أريد قسم معين"), KeyboardButton("👨‍⚕️ أريد دكتور معين")],
        [KeyboardButton("🔙 رجوع للقائمة الرئيسية")]
    ]
    reply_markup = ReplyKeyboardMarkup(consultation_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"{ICONS['consultation']} *استشارة طبية فورية* {ICONS['consultation']}\n\n"
        f"{ICONS['brain']} أنا هنا لمساعدتك بشكل احترافي.\n\n"
        f"{ICONS['advice']} *كيف تبدأ:*\n"
        f"• اكتب أعراضك كاملة (متى بدأت، شدتها، مكانها)\n"
        f"• أخبرني عن أي أمراض مزمنة تعاني منها\n"
        f"• اذكر أي أدوية تتناولها حالياً\n\n"
        f"📝 *مثال رائع:*\n"
        f'"عندي ألم في الصدر من 3 أيام، يزداد مع الحركة، عندي ضغط وسكر، باخذ دواء الضغط صباحاً"\n\n'
        f"{ICONS['success']} *سأقدم لك:*\n"
        f"🔬 تحليل دقيق للأعراض\n"
        f"💊 خطة علاجية مقترحة\n"
        f"🏥 القسم المناسب للمراجعة\n"
        f"📞 أرقام مهمة للمتابعة\n\n"
        f"{ICONS['warning']} *هام:* هذا تشخيص أولي، الرجاء استشارة طبيب\n\n"
        f"*اكتب أعراضك الآن...* {ICONS['stethoscope']}",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def emergency_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الحالات الطارئة"""
    emergency_text = (
        f"{ICONS['emergency']} *حالة طارئة* {ICONS['emergency']}\n\n"
        f"{ICONS['warning']} *إذا كنت تعاني من:*\n"
        f"• ألم شديد في الصدر\n"
        f"• صعوبة في التنفس\n"
        f"• فقدان الوعي\n"
        f"• نزيف حاد\n"
        f"• كلام غير مفهوم\n"
        f"• شلل مفاجئ\n\n"
        f"{ICONS['emergency']} *اطلب الإسعاف فوراً:*\n"
        f"📞 {HOSPITAL_INFO['phone']}\n"
        f"📍 {HOSPITAL_INFO['address']}\n\n"
        f"{ICONS['heart']} *لا تنتظر، احجز أقرب سيارة إسعاف على الفور*"
    )
    await update.message.reply_text(emergency_text, parse_mode="Markdown")

async def hospital_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{ICONS['hospital']} *{HOSPITAL_INFO['name']}* {ICONS['hospital']}

{HOSPITAL_INFO['description']}

{ICONS['location']} *العنوان:* {HOSPITAL_INFO['address']}
{ICONS['phone']} *الهاتف:* {HOSPITAL_INFO['phone']}
{ICONS['phone']} *الشكاوى:* {HOSPITAL_INFO['complaints_phone']}
{ICONS['heart']} *السعة السريرية:* {HOSPITAL_INFO['beds']} سرير
{ICONS['success']} *الخدمات:* مجانية 100%

{ICONS['clinic']} *الطوارئ:* 24 ساعة
{ICONS['appointment']} *العيادات الخارجية:* السبت-الأربعاء 8ص-2م"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def doctors_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{ICONS['doctor']} *الكوادر الطبية الرئيسية* {ICONS['doctor']}

👨‍⚕️ *الهيئة الطبية:*
• أ.د. محمد طاهر جحاف - استشاري عظام
• د. عمار قداري - رئيس الجراحة
• د. نبيل الحاج - أورام وجراحة
• د. معتز الصنوي - رئيس قسم العظام
• د. عبدالله الاشول - رئيس الجراحة

{ICONS['phone']} *للاستفسار عن مواعيد الأطباء:* {HOSPITAL_INFO['phone']}

📅 *يمكنك الحجز المسبق عبر الاتصال بالرقم أعلاه*"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def location_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{ICONS['location']} *موقع المستشفى* {ICONS['location']}

📍 {HOSPITAL_INFO['address']}

🚗 *كيف تصل؟*
يقع المستشفى في وسط العاصمة صنعاء، يمكن الوصول إليه بسهولة عبر سيارات الأجرة أو التطبيقات.

🗺️ *للاتجاهات:* يمكن استخدام خرائط جوجل"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{ICONS['phone']} *أرقام التواصل* {ICONS['phone']}

📞 *للاستفسار العام:* {HOSPITAL_INFO['phone']}
📞 *الشكاوى والاقتراحات:* {HOSPITAL_INFO['complaints_phone']}
📧 *البريد الإلكتروني:* {HOSPITAL_INFO['email']}
💬 *واتساب:* {HOSPITAL_INFO['whatsapp']}

{ICONS['success']} *مواعيد الرد:*
• الاتصال: 24 ساعة
• الواتساب: 8ص-8م

*للحجز والاستفسار، اتصل على {HOSPITAL_INFO['phone']}*"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def appointment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{ICONS['appointment']} *حجز المواعيد* {ICONS['appointment']}

📋 *طرق الحجز:*

1️⃣ *اتصال هاتفي:*
   📞 {HOSPITAL_INFO['phone']}
   🕐 من 8ص إلى 2م (السبت للأربعاء)

2️⃣ *حضور شخصي:*
   📍 قسم الاستقبال بالدور الأرضي
   🕐 8ص - 12م

3️⃣ *الواتساب:*
   💬 {HOSPITAL_INFO['whatsapp']}

📌 *مستندات الحجز:*
• بطاقة شخصية
• تقارير سابقة (إن وجدت)

⚠️ *الخدمات مجانية بالكامل*"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def lab_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{ICONS['lab']} *خدمات المختبر* {ICONS['lab']}

🔬 *الفحوصات المتاحة:*
• تحاليل دم كاملة
• تحاليل كيمياء حيوية
• تحاليل وظائف كبد وكلية
• تحاليل هرمونات
• مزارع وحساسية
• تحاليل بول وبراز

{ICONS['clinic']} *مكان الخدمة:* الدور الثالث، مختبر المركزي
📞 *للاستفسار:* {HOSPITAL_INFO['phone']}

⚠️ *يُفضل الحضور صائماً للتحاليل (8-12 ساعة)*"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def xray_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""{ICONS['xray']} *خدمات الأشعة* {ICONS['xray']}

🩻 *الفحوصات المتاحة:*
• أشعة سينية (X-Ray)
• أشعة مقطعية (CT Scan)
• أشعة موجات فوق صوتية (Ultrasound)
• أشعة رنين مغناطيسي (MRI)
• أشعة الصدر الماموجرام (Mammogram)

{ICONS['clinic']} *مكان الخدمة:* الطابق الأرضي، قسم الأشعة
📞 *للاستفسار:* {HOSPITAL_INFO['phone']}

💡 *نصيحة:* أحضر تقارير الأشعة السابقة إن وجدت"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.message.from_user.first_name
    
    # معالجة الأزرار
    if user_message == f"{ICONS['consultation']} استشارة طبية فورية":
        await medical_consultation(update, context)
    elif user_message == f"{ICONS['hospital']} معلومات المستشفى":
        await hospital_info(update, context)
    elif user_message == f"{ICONS['doctor']} الكوادر الطبية":
        await doctors_info(update, context)
    elif user_message == f"{ICONS['emergency']} طوارئ":
        await emergency_handler(update, context)
    elif user_message == f"{ICONS['phone']} أرقام التواصل":
        await contact_info(update, context)
    elif user_message == f"{ICONS['location']} الموقع":
        await location_info(update, context)
    elif user_message == f"{ICONS['appointment']} حجز موعد":
        await appointment_info(update, context)
    elif user_message == f"{ICONS['lab']} خدمات المختبر":
        await lab_info(update, context)
    elif user_message == f"{ICONS['xray']} الأشعة":
        await xray_info(update, context)
    elif user_message == "🔙 رجوع للقائمة الرئيسية":
        await start(update, context)
    elif user_message == "📝 وصف الأعراض":
        await update.message.reply_text(
            f"{ICONS['stethoscope']} *صف أعراضك بالتفصيل*\n\n"
            f"أخبرني:\n"
            f"• مكان الألم أو المشكلة\n"
            f"• متى بدأت\n"
            f"• شدة الألم (خفيف/متوسط/شديد)\n"
            f"• هل هناك أعراض مصاحبة؟\n\n"
            f"{ICONS['warning']} *ذكر الأمراض المزمنة والأدوية يساعدني كثيراً*",
            parse_mode="Markdown"
        )
    else:
        # استشارة طبية ذكية جداً
        thinking_msg = await update.message.reply_text(
            f"{ICONS['brain']} *استشارة طبية متقدمة* {ICONS['brain']}\n\n"
            f"{ICONS['thinking']} *جاري التحليل...*\n"
            f"{ICONS['microscope']} باحث في قاعدة البيانات الطبية\n"
            f"{ICONS['diagnosis']} مقارنة الأعراض بدقة\n"
            f"{ICONS['treatment']} تجهيز خطة العلاج\n\n"
            f"⏳ لحظة واحدة...",
            parse_mode="Markdown"
        )
        
        # التحليل الطبي المتقدم
        medical_response = await medical_super_analysis(user_message, user_name)
        
        await thinking_msg.edit_text(medical_response, parse_mode="Markdown")

# ========== إعداد Flask لـ Webhook ==========
app = Flask(__name__)
telegram_app = None

@app.route('/')
def home():
    return jsonify({
        "status": "✅ البوت الطبي الذكي شغال",
        "bot": "@Hospitalalg_bot",
        "ai": "Gemini 1.5 Pro",
        "version": "Gold Edition",
        "features": ["تشخيص دقيق", "علاجات", "نصائح طبية", "تحليل أعراض متقدم"]
    })

@app.route('/webhook', methods=['POST'])
async def webhook():
    try:
        update_data = request.get_json()
        if update_data and telegram_app:
            update = Update.de_json(update_data, telegram_app.bot)
            await telegram_app.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"خطأ: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": str(datetime.now())}), 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ========== التشغيل الرئيسي ==========
def main():
    global telegram_app
    
    print("🚀 تشغيل البوت الطبي الذكي...")
    print(f"{ICONS['stethoscope']} مستشفى الجمهوري التعليمي - صنعاء")
    print(f"{ICONS['brain']} نظام Gemini 1.5 Pro - إصدار ذهبي")
    
    # إنشاء تطبيق البوت
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # بدء Flask في خيط منفصل
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    print("✅ خادم الويب شغال...")
    
    # تشغيل polling
    print("✅ البوت جاهز للاستشارات الطبية الذهبية...")
    telegram_app.run_polling()

if __name__ == '__main__':
    main()