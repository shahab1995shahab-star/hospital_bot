import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from google import genai
import asyncio

# ========== إعدادات التسجيل ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== التوكنات والمفاتيح ==========
TELEGRAM_TOKEN = "8743390722:AAFT-L67uXzkipfd-C29-GOBGTHPolHFyX8"
GEMINI_API_KEY = "AIzaSyCWDo3VlPLsTPs5b4zKNzHAmdSC8U29Rsw"

# ========== تشغيل Gemini ==========
client = genai.Client(api_key=GEMINI_API_KEY)

# ========== الأيقونات ==========
I = {
    "hospital": "🏥", "doctor": "👨‍⚕️", "nurse": "👩‍⚕️", "emergency": "🚨",
    "phone": "📞", "location": "📍", "email": "📧", "clock": "🕐",
    "stethoscope": "🩺", "brain": "🧠", "diagnosis": "🔬", "treatment": "💊",
    "warning": "⚠️", "success": "✅", "media": "📺", "facebook": "📘",
    "twitter": "🐦", "instagram": "📷", "youtube": "🎥", "whatsapp": "💬",
    "telegram": "✈️", "info": "ℹ️", "question": "❓", "answer": "✅",
    "department": "📋", "center": "🏛️", "location_pin": "📍", "calendar": "📅"
}

# ========== معلومات المستشفى ==========
HOSPITAL = {
    "name": "هيئة المستشفى الجمهوري التعليمي",
    "full_name": "هيئة المستشفى الجمهوري التعليمي - أمانة العاصمة صنعاء",
    "description": "أقدم وأكبر المستشفيات الحكومية في اليمن، يقدم خدمات طبية مجانية يومياً لمئات الآلاف من المرضى بكادر طبي مؤهل وأجهزة حديثة",
    "beds": "500+ سرير",
    "address": "شارع الزبيري (إسماعيل هنية سابقاً) - أمانة العاصمة صنعاء",
    "phone": "781695995",
    "complaints": "779157779",
    "email": "info@algumhorihosp-san.gov.ye",
    "founded": "من أقدم المستشفيات الحكومية",
    "services": "مجانية"
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

# ========== الأسئلة الشائعة (FAQ) ==========
FAQ = {
    "ما هو المستشفى الجمهوري التعليمي؟": f"{I['hospital']} *المستشفى الجمهوري التعليمي*\n\n{HOSPITAL['description']}\n\n• السعة السريرية: {HOSPITAL['beds']}\n• الخدمات: {HOSPITAL['services']}\n• الموقع: {HOSPITAL['address']}",
    
    "من هو رئيس هيئة المستشفى؟": f"{I['doctor']} *رئيس هيئة المستشفى*\n\n👨‍⚕️ *أ.د. محمد طاهر جحاف*\n📌 استشاري العظام والمفاصل",
    
    "من هم نواب رئيس الهيئة؟": f"{I['doctor']} *نواب رئيس الهيئة*\n\n• د. عمار قداري - للشؤون الفنية\n• د. نبيل الحاج - للشؤون السريرية\n• أ.د. محمد البعداني - للشؤون الأكاديمية",
    
    "ما هي الأقسام الطبية؟": f"{I['department']} *الأقسام الطبية*\n\n• قسم الجراحة العامة\n• قسم العظام والمفاصل\n• قسم الباطنية\n• قسم الأطفال والحضانة\n• قسم العناية المركزة\n• قسم الأنف والأذن والحنجرة\n• قسم الأمراض الجلدية\n• قسم جراحة المخ والأعصاب\n• قسم جراحة المسالك البولية\n• قسم جراحة الوجه والفكين",
    
    "ما هي المراكز الطبية؟": f"{I['center']} *المراكز الطبية المتخصصة*\n\n• مركز الحروق والتجميل\n• مركز الكبد والجهاز الهضمي\n• مركز الأمومة والطفولة\n• مركز طب وجراحة العيون\n• مركز الغسيل الكلوي\n• مركز الحميات\n• مركز الطوارئ العامة\n• مركز العلاج الطبيعي والإبر الصينية",
    
    "هل الخدمات مجانية؟": f"{I['success']} *الخدمات المجانية*\n\nنعم، يقدم المستشفى خدماته الطبية *مجاناً* للمرضى في معظم الأقسام.\n\n{ I['warning'] } بعض الخدمات المتخصصة قد تتطلب رسوماً رمزية.",
    
    "أين يقع المستشفى؟": f"{I['location_pin']} *موقع المستشفى*\n\n📍 {HOSPITAL['address']}\n\nوسط العاصمة صنعاء - يسهل الوصول إليه",
    
    "كيف يمكن التواصل؟": f"{I['phone']} *طرق التواصل*\n\n📞 هاتف: {HOSPITAL['phone']}\n📞 للشكاوى: {HOSPITAL['complaints']}\n📧 البريد الإلكتروني: {HOSPITAL['email']}",
    
    "هل توجد عيادات خارجية؟": f"{I['clock']} *العيادات الخارجية*\n\nنعم، يوجد قسم خاص بالعيادات الخارجية بإدارة مختصة لتقديم الخدمات اليومية للمرضى.\n\n🕐 أوقات العمل: السبت - الأربعاء (8ص - 2م)"
}

# ========== دالة التحليل الطبي باستخدام Gemini (بأحدث نموذج) ==========
async def medical_analysis(symptoms):
    """تحليل الأعراض باستخدام Gemini AI"""
    try:
        prompt = f"""أنت استشاري طبي متخصص في {HOSPITAL['name']}.

الأعراض التي يشكو منها المريض: {symptoms}

قم بتحليل هذه الأعراض وتقديم استشارة طبية أولية بهذا التنسيق بالضبط:

🩺 *الاستشارة الطبية*

🧠 *تحليل الأعراض:*
[اكتب تحليلاً دقيقاً وواضحاً للأعراض المذكورة]

🔬 *التشخيص المبدئي (احتمالات):*
• [الاحتمال الأول]
• [الاحتمال الثاني]

💊 *العلاج والنصائح الأولية:*
• [نصيحة عملية 1]
• [نصيحة عملية 2]

🏥 *القسم الطبي المناسب للمراجعة:*
[اسم القسم المناسب]

⚠️ *هذا تشخيص أولي وليس بديلاً عن استشارة الطبيب المختص*

📞 للطوارئ: {HOSPITAL['phone']}
📍 {HOSPITAL['address']}"""

        # استخدام أحدث نموذج متاح
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",  # أحدث نموذج
            contents=prompt
        )
        return response.text if response else None
    except Exception as e:
        logger.error(f"خطأ في Gemini: {e}")
        # محاولة استخدام نموذج آخر
        try:
            response = client.models.generate_content(
                model="gemini-1.5-pro",  # نموذج بديل
                contents=prompt
            )
            return response.text if response else None
        except Exception as e2:
            logger.error(f"خطأ في Gemini (نموذج بديل): {e2}")
            return None

# ========== دوال البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب والقائمة الرئيسية"""
    keyboard = [
        [KeyboardButton(f"{I['stethoscope']} استشارة طبية"), KeyboardButton(f"{I['question']} الأسئلة الشائعة")],
        [KeyboardButton(f"{I['hospital']} معلومات المستشفى"), KeyboardButton(f"{I['doctor']} الكوادر الطبية")],
        [KeyboardButton(f"{I['department']} الأقسام"), KeyboardButton(f"{I['center']} المراكز")],
        [KeyboardButton(f"{I['emergency']} طوارئ"), KeyboardButton(f"{I['phone']} التواصل")],
        [KeyboardButton(f"{I['location']} الموقع"), KeyboardButton(f"{I['media']} المركز الإعلامي")],
        [KeyboardButton(f"{I['whatsapp']} واتساب مباشر")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = f"""
🏥 *{HOSPITAL['full_name']}* 🏥

{ I['info'] } *مرحباً بك في البوت الرسمي لهيئة المستشفى الجمهوري التعليمي*

{ I['stethoscope'] } *بوت طبي ذكي بالذكاء الاصطناعي Gemini*

{ I['success'] } *الخدمات التي نقدمها:*
• 🔬 تحليل دقيق للأعراض الطبية
• 💊 تشخيص مبدئي وعلاجات ونصائح
• 🏥 توجيه للقسم الطبي المناسب
• 📋 معلومات شاملة عن المستشفى
• 👨‍⚕️ الكوادر الطبية والأقسام
• 📺 المركز الإعلامي ووسائل التواصل

{ I['emergency'] } *للطوارئ:* `{HOSPITAL['phone']}`

📝 *اكتب أعراضك أو اختر من القائمة أدناه*

{ I['warning'] } *تنبيه:* هذا البوت يقدم استشارات أولية وليس بديلاً عن زيارة الطبيب المختص
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def hospital_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات شاملة عن المستشفى"""
    text = f"""
{I['hospital']} *{HOSPITAL['full_name']}* {I['hospital']}

📖 *نبذة تعريفية:*
{HOSPITAL['description']}

📊 *إحصائيات:*
• 🛏️ السعة السريرية: {HOSPITAL['beds']}
• 💉 الخدمات: {HOSPITAL['services']}
• 📅 التأسيس: {HOSPITAL['founded']}

📍 *العنوان:*
{HOSPITAL['address']}

📞 *للتواصل:*
{ HOSPITAL['phone'] }

⚕️ *الرؤية:* الريادة في تقديم الخدمات الصحية المجانية على مستوى الجمهورية اليمنية

💝 *الرسالة:* تقديم خدمات صحية مجانية بجودة عالية عبر كادر مؤهل خبير
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def doctors_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الكوادر الطبية"""
    text = f"""
{I['doctor']} *الكوادر الطبية الرئيسية* {I['doctor']}

👨‍⚕️ *رئيس الهيئة:*
• أ.د. محمد طاهر جحاف - استشاري العظام والمفاصل

👨‍⚕️ *نواب رئيس الهيئة:*
• د. عمار قداري - الشؤون الفنية
• د. نبيل الحاج - الشؤون السريرية
• أ.د. محمد البعداني - الشؤون الأكاديمية

👨‍⚕️ *رؤساء الأقسام:*
• د/سمير العريقي - جراحة المخ والأعصاب
• د/معتز الصنوي - قسم العظام
• د/عبدالله الاشول - الجراحة العامة
• د/زين العابدين جروش - المسالك البولية
• د/عبد الواسع مجاهد - الباطنية
• د/ناشر الاغبري - الأطفال والحضانة

{I['info']} *للاستفسار عن مواعيد الأطباء:* 📞 {HOSPITAL['phone']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def departments_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأقسام الطبية"""
    text = f"""
{I['department']} *الأقسام الطبية في المستشفى* {I['department']}

🏥 *الأقسام الرئيسية:*

• 🔪 الجراحة العامة
• 🦴 العظام والمفاصل
• 🫀 الباطنية
• 👶 الأطفال والحضانة
• 💓 العناية المركزة (ICU)
• 👂 الأنف والأذن والحنجرة
• 🩹 الأمراض الجلدية
• 🧠 جراحة المخ والأعصاب
• 💧 جراحة المسالك البولية
• 😷 جراحة الوجه والفكين
• 👁️ طب وجراحة العيون
• 🚨 الطوارئ العامة

📞 *للاستفسار:* {HOSPITAL['phone']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def centers_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المراكز الطبية المتخصصة"""
    text = f"""
{I['center']} *المراكز الطبية المتخصصة* {I['center']}

• 🔥 مركز الحروق والتجميل
• 🫀 مركز الكبد والجهاز الهضمي
• 🤱 مركز الأمومة والطفولة
• 👁️ مركز طب وجراحة العيون
• 💊 مركز الغسيل الكلوي
• 🦠 مركز الحميات
• 🚑 مركز الطوارئ العامة
• 💆 مركز العلاج الطبيعي والإبر الصينية
• 🦷 مركز طب الأسنان الاستشاري
• 🔬 مركز الوسائل التشخيصية

{I['info']} *جميع المراكز تقدم خدماتها مجاناً للمواطنين*
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def emergency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حالات الطوارئ"""
    text = f"""
{I['emergency']} *حالة طارئة - تعليمات مهمة* {I['emergency']}

⚠️ *إذا كنت تعاني من أحد الأعراض التالية:*

• ألم شديد في الصدر يمتد للذراع
• صعوبة شديدة في التنفس
• فقدان الوعي أو الإغماء
• نزيف حاد غير متوقف
• شلل مفاجئ في نصف الجسم
• كلام غير مفهوم فجأة
• حروق من الدرجة الثالثة

🚨 *اتصل فوراً على الطوارئ:* `{HOSPITAL['phone']}`

📍 *العنوان:* {HOSPITAL['address']}

🩺 *لا تنتظر - اذهب لأقرب قسم طوارئ فوراً*

{ I['warning'] } *هذه الحالة تستدعي تدخلاً طبياً عاجلاً*
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات التواصل"""
    text = f"""
{I['phone']} *طرق التواصل مع المستشفى* {I['phone']}

📞 *الرقم الرئيسي:* `{HOSPITAL['phone']}`
📞 *الشكاوى والاقتراحات:* `{HOSPITAL['complaints']}`
📧 *البريد الإلكتروني:* `{HOSPITAL['email']}`

💬 *واتساب مباشر:* [اضغط هنا للتواصل]({SOCIAL_MEDIA['whatsapp_direct']})

🕐 *أوقات الاتصال:*
• الطوارئ: 24 ساعة
• الاستفسارات العامة: 8ص - 8م
• الشكاوى: 9ص - 3م

{I['success']} *فريقنا يخدمك على مدار الساعة*
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def location_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """موقع المستشفى"""
    text = f"""
{I['location_pin']} *موقع هيئة المستشفى الجمهوري التعليمي* {I['location_pin']}

📍 *العنوان التفصيلي:*
{HOSPITAL['address']}

🗺️ *معالم قريبة:*
• يقع في وسط العاصمة صنعاء
• قريب من كلية الطب
• يمكن الوصول إليه بسهولة عبر وسائل النقل

🚗 *كيف تصل؟*
يمكن استخدام تطبيقات الخرائط للوصول إلى المستشفى

📞 *للاستفسار عن الاتجاهات:* {HOSPITAL['phone']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def faq_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة الأسئلة الشائعة"""
    keyboard = []
    for question in FAQ.keys():
        keyboard.append([InlineKeyboardButton(f"{I['question']} {question}", callback_data=f"faq_{question}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{I['question']} *الأسئلة الشائعة* {I['question']}\n\n"
        f"اختر سؤالك من القائمة أدناه:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def faq_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على سؤال من الأسئلة الشائعة"""
    query = update.callback_query
    await query.answer()
    
    question = query.data.replace("faq_", "")
    answer = FAQ.get(question, "عذراً، لم يتم العثور على إجابة لهذا السؤال.")
    
    await query.edit_message_text(
        f"{I['answer']} *{question}*\n\n{answer}\n\n"
        f"{I['info']} للعودة إلى الأسئلة الشائعة، استخدم الأمر /start",
        parse_mode="Markdown"
    )

async def consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء استشارة طبية"""
    await update.message.reply_text(
        f"{I['stethoscope']} *استشارة طبية فورية بالذكاء الاصطناعي* {I['stethoscope']}\n\n"
        f"📝 *اكتب أعراضك بالتفصيل:*\n"
        f"• متى بدأت الأعراض؟\n"
        f"• ما هي شدتها؟\n"
        f"• أين مكان الألم؟\n"
        f"• هل هناك أعراض مصاحبة؟\n\n"
        f"📝 *مثال:*\n"
        f"'عندي ألم في الصدر من 3 أيام، يزداد مع الحركة، وعندي ضغط وسكر'\n\n"
        f"{I['brain']} *سأقوم بتحليل أعراضك وتقديم استشارة طبية أولية*\n\n"
        f"{I['warning']} *تنبيه:* هذا تشخيص أولي وليس بديلاً عن استشارة الطبيب المختص",
        parse_mode="Markdown"
    )

async def media_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المركز الإعلامي"""
    text = f"""
{I['media']} *المركز الإعلامي - هيئة المستشفى الجمهوري التعليمي* {I['media']}

📺 *تابعونا على جميع وسائل التواصل الاجتماعي:*

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
📞 *للاستفسار:* {HOSPITAL['phone']}
📍 *العنوان:* {HOSPITAL['address']}
"""
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)

async def whatsapp_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """واتساب مباشر"""
    text = f"""
{I['whatsapp']} *تواصل مباشر عبر الواتساب* {I['whatsapp']}

📱 *للتواصل المباشر مع فريق المستشفى:*

[اضغط هنا للتواصل عبر الواتساب]({SOCIAL_MEDIA['whatsapp_direct']})

💬 *يمكنك استخدام هذه الخدمة لـ:*
• ✅ حجز المواعيد
• ✅ الاستفسار عن الخدمات
• ✅ تقديم الملاحظات والاقتراحات
• ✅ الاستعلام عن نتائج التحاليل
• ✅ متابعة الحالات المرضية

📞 *أو اتصل على:* {HOSPITAL['phone']}

🕐 *أوقات الرد على الواتساب:* 9ص - 5م (السبت - الأربعاء)
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    msg = update.message.text
    
    # معالجة الأزرار الرئيسية
    if msg == f"{I['stethoscope']} استشارة طبية":
        await consultation(update, context)
    elif msg == f"{I['question']} الأسئلة الشائعة":
        await faq_list(update, context)
    elif msg == f"{I['hospital']} معلومات المستشفى":
        await hospital_info(update, context)
    elif msg == f"{I['doctor']} الكوادر الطبية":
        await doctors_info(update, context)
    elif msg == f"{I['department']} الأقسام":
        await departments_info(update, context)
    elif msg == f"{I['center']} المراكز":
        await centers_info(update, context)
    elif msg == f"{I['emergency']} طوارئ":
        await emergency(update, context)
    elif msg == f"{I['phone']} التواصل":
        await contact_info(update, context)
    elif msg == f"{I['location']} الموقع":
        await location_info(update, context)
    elif msg == f"{I['media']} المركز الإعلامي":
        await media_center(update, context)
    elif msg == f"{I['whatsapp']} واتساب مباشر":
        await whatsapp_direct(update, context)
    else:
        # استشارة طبية ذكية
        thinking = await update.message.reply_text(
            f"{I['brain']} *جاري تحليل أعراضك وتجهيز الاستشارة الطبية...*\n\n"
            f"🩺 يرجى الانتظار لحظات",
            parse_mode="Markdown"
        )
        
        response = await medical_analysis(msg)
        
        if response:
            await thinking.edit_text(response, parse_mode="Markdown")
        else:
            await thinking.edit_text(
                f"{I['warning']} *عذراً، حدث خطأ في خدمة الذكاء الاصطناعي*\n\n"
                f"يمكنك استخدام الأزرار للحصول على المعلومات المباشرة.\n\n"
                f"📞 *للاستفسار المباشر:* {HOSPITAL['phone']}\n\n"
                f"💡 *نصيحة:* حاول كتابة الأعراض بشكل أوضح مع التفاصيل (المكان، المدة، الشدة)\n\n"
                f"أو اضغط على زر *{I['stethoscope']} استشارة طبية* واتبع التعليمات",
                parse_mode="Markdown"
            )

# ========== إعداد Flask و Webhook ==========
app = Flask(__name__)

# إنشاء تطبيق Telegram
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# إضافة المعالجات
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(faq_callback, pattern="^faq_"))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/')
def home():
    return jsonify({
        "status": "✅ البوت الطبي الذكي شغال",
        "bot": "@Hospitalalg_bot",
        "name": "هيئة المستشفى الجمهوري التعليمي",
        "version": "Golden Edition v2.0",
        "ai": "Gemini 2.0 Flash Exp",
        "features": ["استشارات طبية", "أسئلة شائعة", "معلومات المستشفى", "الكوادر الطبية", "المركز الإعلامي"]
    })

@app.route('/webhook', methods=['POST'])
async def webhook():
    """استقبال التحديثات من Telegram"""
    try:
        update_data = request.get_json()
        if update_data:
            async with telegram_app:
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
def run_webhook_mode():
    """تشغيل وضع Webhook"""
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"🚀 تشغيل بوت هيئة المستشفى الجمهوري التعليمي...")
    logger.info(f"📍 Port: {port}")
    logger.info(f"🤖 AI: Google Gemini 2.0 Flash Exp")
    logger.info(f"📱 Bot: @Hospitalalg_bot")
    
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    run_webhook_mode()
