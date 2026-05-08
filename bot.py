import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import re

# ========== إعدادات التسجيل ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== التوكن ==========
TELEGRAM_TOKEN = "8743390722:AAFT-L67uXzkipfd-C29-GOBGTHPolHFyX8"

# ========== الأيقونات ==========
I = {
    "hospital": "🏥", "doctor": "👨‍⚕️", "emergency": "🚨", "phone": "📞",
    "location": "📍", "email": "📧", "clock": "🕐", "stethoscope": "🩺",
    "warning": "⚠️", "success": "✅", "media": "📺", "facebook": "📘",
    "twitter": "🐦", "instagram": "📷", "youtube": "🎥", "whatsapp": "💬",
    "telegram": "✈️", "info": "ℹ️", "question": "❓", "answer": "✅",
    "department": "📋", "center": "🏛️", "location_pin": "📍", "calendar": "📅",
    "blood": "🩸", "heart": "❤️", "brain": "🧠", "bone": "🦴", "eye": "👁️",
    "ear": "👂", "nose": "👃", "child": "👶", "old": "👴", "woman": "👩",
    "man": "👨", "injection": "💉", "operation": "🔪", "ambulance": "🚑"
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
    "whatsapp": "http://wa.me/967734734696",
    "founded": "من أقدم المستشفيات الحكومية",
    "services": "مجانية",
    "emergency_24": "نعم، 24 ساعة"
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
DEPARTMENTS = {
    "الجراحة العامة": ["جراحة", "عملية", "فتق", "زائدة", "مرارة", "ورم", "كيس", "خراج", "استئصال", "غدة"],
    "العظام والمفاصل": ["عظم", "كسر", "مفصل", "ظهر", "عمود فقري", "ركبة", "كتف", "يد", "رجل", "قدم", "الديسك", "غضروف", "خشونة", "عرق النسا"],
    "الباطنية": ["ضغط", "سكر", "قلب", "صدر", "كبد", "معده", "قولون", "اسهال", "امساك", "حمى", "سخونة", "غثيان", "قيء", "كحة", "زكام", "انفلونزا"],
    "الأطفال والحضانة": ["طفل", "رضيع", "صغير", "حضانة", "تطعيم", "لقاح", "حرارة طفل", "اسهال اطفال", "تقيؤ اطفال", "تبول لا إرادي"],
    "العناية المركزة": ["عناية", "ICU", "حالة خطيرة", "تنفس صناعي", "غيبوبة", "فشل عضوي"],
    "الأنف والأذن والحنجرة": ["أذن", "أنف", "حنجرة", "سمع", "لوز", "زكام مزمن", "جيوب", "بلعوم", "صوت", "شخير"],
    "الأمراض الجلدية": ["جلد", "حكة", "طفح", "حبوب", "قشرة", "اكزيما", "صدفية", "بهاق", "ثعلبة", "فطريات", "حساسية جلد"],
    "جراحة المخ والأعصاب": ["مخ", "أعصاب", "دماغ", "صداع مزمن", "شقيقة", "دوار", "صرع", "تشنج", "تنميل", "شلل", "رعاش", "زلال"],
    "جراحة المسالك البولية": ["مسالك", "بول", "كلية", "حصوة", "تبول", "بروستاتا", "خصية", "حرقة بول", "سلس بول", "ضعف جنسي"],
    "جراحة الوجه والفكين": ["فك", "وجه", "فم", "لثة", "ضرس", "اسنان", "تقويم", "ابتسامة", "فكين"],
    "العيون": ["عين", "بصر", "نظر", "رمد", "جفن", "ألم عين", "جفاف", "مياه زرقاء", "كتاركت", "ليزك"],
    "الطوارئ العامة": ["طوارئ", "اسعاف", "حادث", "اصابة", "نزيف", "جرح", "رض", "اختناق", "غصة"],
    "الحميات": ["حمى", "تيفود", "ملاريا", "دينجي", "فيروس", "عدوى", "التهاب كبد", "حمى صفراء", "كوليرا"],
    "الغسيل الكلوي": ["كلية", "غسيل", "دياليز", "فشل كلوي", "يوريميا", "كرياتينين"],
    "الجهاز الهضمي والكبد": ["كبد", "معده", "قولون", "سوء هضم", "قرحة", "التهاب كبد", "صفار", "مرارة", "بنكرياس"],
    "الحروق والتجميل": ["حرق", "تجميل", "ندبة", "تشوه", "بشرة", "حروق", "ترميم"],
    "العلاج الطبيعي": ["علاج طبيعي", "فيزيائي", "تأهيل", "تمارين", "إعادة تأهيل", "طبيعي"]
}

# ========== الكوادر الطبية ==========
DOCTORS = {
    "رئيس الهيئة": {"name": "أ.د. محمد طاهر جحاف", "specialty": "استشاري العظام والمفاصل", "phone": None},
    "نائب رئيس الهيئة للشؤون الفنية": {"name": "د. عمار قداري", "specialty": "رئيس قسم الجراحة", "phone": None},
    "نائب رئيس الهيئة للشؤون السريرية": {"name": "د. نبيل الحاج", "specialty": "اخصائي جراحة واورام", "phone": None},
    "نائب رئيس الهيئة للشؤون الأكاديمية": {"name": "أ.د. محمد البعداني", "specialty": "طب عام وجراحة", "phone": None},
    "رئيس قسم جراحة المخ والأعصاب": {"name": "د/سمير العريقي", "specialty": "جراحة المخ والأعصاب", "phone": None},
    "رئيس قسم العظام": {"name": "د/معتز الصنوي", "specialty": "جراحة العظام", "phone": None},
    "رئيس قسم الجراحة العامة": {"name": "د/عبدالله الاشول", "specialty": "الجراحة العامة", "phone": None},
    "رئيس قسم المسالك البولية": {"name": "د/زين العابدين جروش", "specialty": "جراحة المسالك البولية", "phone": None},
    "رئيس قسم الباطنية": {"name": "د/عبد الواسع مجاهد", "specialty": "الباطنية", "phone": None},
    "رئيس قسم الأطفال والحضانة": {"name": "د/ناشر الاغبري", "specialty": "طب الأطفال", "phone": None},
    "مدير مركز الطوارئ العامة": {"name": "د/ياسر البريهي", "specialty": "الطوارئ", "phone": None}
}

# ========== المراكز الطبية ==========
CENTERS = {
    "مركز الحروق والتجميل": "يقدم خدمات علاج الحروق والترميم والتجميل",
    "مركز الكبد والجهاز الهضمي": "متخصص في أمراض الكبد والجهاز الهضمي",
    "مركز الأمومة والطفولة": "يقدم خدمات رعاية الأمومة والطفل",
    "مركز طب وجراحة العيون": "متخصص في علاج وجراحة العيون",
    "مركز الغسيل الكلوي": "يقدم خدمات الغسيل الكلوي للمرضى",
    "مركز الحميات": "متخصص في الأمراض المعدية والحميات",
    "مركز الطوارئ العامة": "يستقبل الحالات الطارئة 24 ساعة",
    "مركز العلاج الطبيعي": "يقدم خدمات العلاج الطبيعي والتأهيل",
    "مركز طب الأسنان الاستشاري": "متخصص في طب الأسنان",
    "مركز الوسائل التشخيصية": "يقدم خدمات الأشعة والتحاليل"
}

# ========== الأسئلة الشائعة والإجابات (قاعدة بيانات ضخمة) ==========
FAQ_DATABASE = {
    # أسئلة عن المستشفى
    "ما هو المستشفى الجمهوري التعليمي": f"{I['hospital']} *المستشفى الجمهوري التعليمي*\n\n{HOSPITAL['description']}",
    "وصف المستشفى": f"{I['info']} *وصف المستشفى*\n\n{HOSPITAL['description']}",
    "معلومات عن المستشفى": f"{I['hospital']} *معلومات عن المستشفى*\n\n{HOSPITAL['description']}\n\n• السعة السريرية: {HOSPITAL['beds']}\n• الخدمات: مجانية\n• الطوارئ: {HOSPITAL['emergency_24']}",
    
    # أسئلة عن الموقع
    "اين يقع المستشفى": f"{I['location']} *موقع المستشفى*\n📍 {HOSPITAL['address']}",
    "موقع المستشفى": f"{I['location']} *الموقع*\n📍 {HOSPITAL['address']}\n\nوسط العاصمة صنعاء، يسهل الوصول إليه",
    "عنوان المستشفى": f"{I['location']} *العنوان*\n📍 {HOSPITAL['address']}",
    
    # أسئلة عن التواصل
    "رقم المستشفى": f"{I['phone']} *رقم الهاتف*\n📞 {HOSPITAL['phone']}",
    "ارقام التواصل": f"{I['phone']} *أرقام التواصل*\n📞 للاستفسار: {HOSPITAL['phone']}\n📞 للشكاوى: {HOSPITAL['complaints']}",
    "بريد المستشفى": f"{I['email']} *البريد الإلكتروني*\n📧 {HOSPITAL['email']}",
    "واتساب المستشفى": f"{I['whatsapp']} *واتساب*\n💬 [تواصل عبر الواتساب]({HOSPITAL['whatsapp']})",
    
    # أسئلة عن الخدمات
    "هل الخدمات مجانية": f"{I['success']} *الخدمات المجانية*\nنعم، يقدم المستشفى خدماته الطبية *مجاناً* للمرضى في معظم الأقسام.",
    "الخدمات المجانية": f"{I['success']} *الخدمات المجانية*\nيقدم المستشفى خدمات طبية مجانية للمواطنين",
    "عيادات خارجية": f"{I['clock']} *العيادات الخارجية*\nنعم، يوجد قسم خاص بالعيادات الخارجية.\n🕐 أوقات العمل: السبت - الأربعاء (8ص - 2م)",
    "مواعيد العيادات": f"{I['calendar']} *مواعيد العيادات الخارجية*\nالسبت إلى الأربعاء: 8 صباحاً - 2 ظهراً",
    "الطوارئ": f"{I['emergency']} *قسم الطوارئ*\nيعمل 24 ساعة طوال أيام الأسبوع\n📞 {HOSPITAL['phone']}",
    "ارقام الطوارئ": f"{I['emergency']} *رقم الطوارئ*\n📞 {HOSPITAL['phone']}",
    
    # أسئلة عن الكوادر
    "رئيس الهيئة": f"{I['doctor']} *رئيس هيئة المستشفى*\n👨‍⚕️ {DOCTORS['رئيس الهيئة']['name']}\n📌 {DOCTORS['رئيس الهيئة']['specialty']}",
    "من هو رئيس الهيئة": f"{I['doctor']} *رئيس هيئة المستشفى*\n👨‍⚕️ أ.د. محمد طاهر جحاف\nاستشاري العظام والمفاصل",
    "نواب رئيس الهيئة": f"{I['doctor']} *نواب رئيس الهيئة*\n• د. عمار قداري - الشؤون الفنية\n• د. نبيل الحاج - الشؤون السريرية\n• أ.د. محمد البعداني - الشؤون الأكاديمية",
    "الكوادر الطبية": f"{I['doctor']} *الكوادر الطبية*\n" + "\n".join([f"• {doc['name']} - {doc['specialty']}" for doc in DOCTORS.values()]),
    "أطباء المستشفى": f"{I['doctor']} *أطباء المستشفى*\n" + "\n".join([f"• {doc['name']} ({doc['specialty']})" for doc in DOCTORS.values()]),
    
    # أسئلة عن الأقسام
    "الاقسام الطبية": f"{I['department']} *الأقسام الطبية*\n" + "\n".join([f"• {dept}" for dept in DEPARTMENTS.keys()]),
    "اقسام المستشفى": f"{I['department']} *أقسام المستشفى*\n" + "\n".join([f"• {dept}" for dept in DEPARTMENTS.keys()]),
    "قسم الجراحة": "🔪 *قسم الجراحة العامة*\nيدير القسم: د/عبدالله الاشول",
    "قسم العظام": "🦴 *قسم العظام والمفاصل*\nيدير القسم: د/معتز الصنوي",
    "قسم الباطنية": "🫀 *قسم الباطنية*\nيدير القسم: د/عبد الواسع مجاهد",
    "قسم الاطفال": "👶 *قسم الأطفال والحضانة*\nيدير القسم: د/ناشر الاغبري",
    "قسم الطوارئ": "🚨 *قسم الطوارئ العامة*\nيدير القسم: د/ياسر البريهي\nيعمل 24 ساعة",
    
    # أسئلة عن المراكز
    "المراكز الطبية": f"{I['center']} *المراكز الطبية*\n" + "\n".join([f"• {center}" for center in CENTERS.keys()]),
    "مراكز المستشفى": f"{I['center']} *المراكز المتخصصة*\n" + "\n".join([f"• {center}" for center in CENTERS.keys()]),
    "مركز الحروق": "🔥 *مركز الحروق والتجميل*\nيقدم خدمات علاج الحروق والترميم",
    "مركز الكبد": "🫀 *مركز الكبد والجهاز الهضمي*\nمتخصص في أمراض الكبد والجهاز الهضمي",
    "مركز العيون": "👁️ *مركز طب وجراحة العيون*\nمتخصص في علاج وجراحة العيون",
    "مركز الغسيل الكلوي": "💊 *مركز الغسيل الكلوي*\nيقدم خدمات الغسيل الكلوي للمرضى",
    
    # نصائح عامة
    "نصيحة": f"{I['warning']} *نصائح صحية*\n• حافظ على نظافة يديك\n• تناول غذاء صحي متوازن\n• اشرب كمية كافية من الماء\n• مارس الرياضة بانتظام\n• لا تهمل الأعراض الخطيرة",
    "صحتك": f"{I['heart']} *اهتمام بصحتك*\nلا تتردد في زيارة الطبيب عند الشعور بأي أعراض مزعجة\nالوقاية خير من العلاج",
    "شكرا": f"{I['success']} *على الرحب والسعة!*\nنتمنى لك دوام الصحة والعافية 🌹",
    "thank you": f"{I['success']} *You're welcome!*\nWe wish you continued health and wellness 🌹"
}

# ========== دالة البحث عن إجابة ==========
def find_answer(question):
    """البحث عن إجابة في قاعدة البيانات"""
    question_lower = question.lower().strip()
    
    # البحث المباشر
    for key, answer in FAQ_DATABASE.items():
        if key.lower() in question_lower:
            return answer
    
    # البحث عن الكلمات المفتاحية
    keywords_map = {
        "رقم": ["رقم", "هاتف", "تليفون", "تواصل", "اتصال"],
        "موقع": ["موقع", "عنوان", "مكان", "وين", "أين", "اين"],
        "مواعيد": ["مواعيد", "دوام", "ساعات", "وقت العمل", "أوقات", "اوقات"],
        "مجاني": ["مجاني", "مجانا", "ببلاش", "بدون فلوس"],
        "طوارئ": ["طوارئ", "اسعاف", "إسعاف", "حادث", "حالة خطيرة"],
        "عيادات": ["عيادات", "عيادة", "خارجية"],
        "جراحة": ["جراحة", "عمليات", "عملية"],
        "عظام": ["عظام", "كسور", "مفاصل", "ظهر"],
        "اطفال": ["اطفال", "أطفال", "طفل", "رضع", "حضانة"],
        "باطنية": ["باطنية", "ضغط", "سكر", "قلب", "صدر"],
        "عين": ["عين", "عيون", "نظر", "بصر", "رمد"],
        "جلدية": ["جلد", "جلدية", "حكة", "طفح", "حساسية"],
        "مسالك": ["مسالك", "بول", "كلية", "بروستاتا"],
        "حروق": ["حروق", "حرق", "تجميل"],
        "كبد": ["كبد", "جهاز هضمي", "معده", "قولون"],
        "غسيل كلوي": ["غسيل كلوي", "دياليز", "فشل كلوي"],
        "رئيس": ["رئيس", "مدير", "الهيئة", "جحاف"],
        "نواب": ["نواب", "نائب", "قداري", "حاج", "بعداني"],
        "مركز": ["مركز", "مراكز", "مركز الطوارئ", "مركز الحميات"]
    }
    
    for category, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword in question_lower:
                for key, answer in FAQ_DATABASE.items():
                    if category in key.lower():
                        return answer
    
    return None

# ========== دالة تحديد القسم حسب الأعراض ==========
def find_department(symptoms):
    """توجيه المريض للقسم المناسب حسب الأعراض"""
    symptoms_lower = symptoms.lower()
    
    # كلمات تدل على حالات خطيرة
    emergency_words = ["نزيف حاد", "فقد وعي", "لا يتنفس", "نوبة قلبية", "سكتة", "غيبوبة", "جرح عميق", "حروق شديدة", "ألم شديد في الصدر"]
    for word in emergency_words:
        if word in symptoms_lower:
            return "🚨 *الطوارئ العامة* - حالة خطيرة تستدعي التدخل الفوري"
    
    # البحث في الأقسام
    for dept, keywords in DEPARTMENTS.items():
        for keyword in keywords:
            if keyword in symptoms_lower:
                return f"🏥 *{dept}*\n\n{I['info']} هذا القسم هو الأنسب لتشخيص وعلاج الحالة التي تعاني منها."
    
    # أقسام محددة حسب كلمات دقيقة
    if "صداع" in symptoms_lower or "شقيقة" in symptoms_lower or "دوار" in symptoms_lower:
        return "🏥 *جراحة المخ والأعصاب*\nأو *الباطنية* (إذا كان الصداع مرتبطاً بالضغط)"
    elif "حرارة" in symptoms_lower or "حمى" in symptoms_lower:
        return "🏥 *الباطنية* أو *الحميات*\nيفضل مراجعة الباطنية أولاً"
    elif "طفل" in symptoms_lower or "رضيع" in symptoms_lower:
        return "🏥 *قسم الأطفال والحضانة*"
    elif "حامل" in symptoms_lower or "ولادة" in symptoms_lower:
        return "🏥 *مركز الأمومة والطفولة*"
    
    return None

# ========== دوال البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب والقائمة الرئيسية"""
    keyboard = [
        [KeyboardButton(f"{I['question']} أسئلة شائعة"), KeyboardButton(f"{I['stethoscope']} استشارة وتوجيه")],
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

{ I['success'] } *لخدمتك على مدار الساعة*

*يمكنك:*
• {I['question']} طرح الأسئلة والاستفسارات
• {I['stethoscope']} وصف الأعراض لتوجيهك للقسم المناسب
• {I['info']} الحصول على معلومات عن المستشفى والخدمات

{ I['emergency'] } *للطوارئ:* `{HOSPITAL['phone']}`

📝 *اكتب سؤالك أو أعراضك أو اختر من القائمة أدناه*
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة الأسئلة الشائعة"""
    keyboard = [
        [InlineKeyboardButton("🏥 معلومات عن المستشفى", callback_data="faq_info")],
        [InlineKeyboardButton("📍 موقع ورقم المستشفى", callback_data="faq_contact")],
        [InlineKeyboardButton("👨‍⚕️ رئيس ونواب الهيئة", callback_data="faq_doctors")],
        [InlineKeyboardButton("📋 الأقسام الطبية", callback_data="faq_departments")],
        [InlineKeyboardButton("🏛️ المراكز الطبية", callback_data="faq_centers")],
        [InlineKeyboardButton("🕐 مواعيد العيادات", callback_data="faq_timing")],
        [InlineKeyboardButton("💰 هل الخدمات مجانية؟", callback_data="faq_free")],
        [InlineKeyboardButton("🚨 الطوارئ", callback_data="faq_emergency")],
        [InlineKeyboardButton("💬 واتساب مباشر", callback_data="faq_whatsapp")],
        [InlineKeyboardButton("📺 المركز الإعلامي", callback_data="faq_media")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{I['question']} *الأسئلة الشائعة* {I['question']}\n\nاختر ما تريد معرفته:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def faq_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأسئلة الشائعة"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    response = ""
    
    if data == "faq_info":
        response = f"{I['hospital']} *{HOSPITAL['full_name']}*\n\n{HOSPITAL['description']}\n\n• السعة السريرية: {HOSPITAL['beds']}\n• الخدمات: مجانية"
    elif data == "faq_contact":
        response = f"{I['location']} *الموقع:* {HOSPITAL['address']}\n\n{I['phone']} *رقم الهاتف:* {HOSPITAL['phone']}\n📞 *الشكاوى:* {HOSPITAL['complaints']}\n📧 *البريد:* {HOSPITAL['email']}"
    elif data == "faq_doctors":
        response = f"{I['doctor']} *الكوادر الطبية*\n\n• *رئيس الهيئة:* أ.د. محمد طاهر جحاف (عظام)\n• *نائب رئيس الهيئة (فني):* د. عمار قداري\n• *نائب رئيس الهيئة (سريري):* د. نبيل الحاج\n• *نائب رئيس الهيئة (أكاديمي):* أ.د. محمد البعداني"
    elif data == "faq_departments":
        depts = "\n".join([f"• {d}" for d in DEPARTMENTS.keys()])
        response = f"{I['department']} *الأقسام الطبية*\n\n{depts}"
    elif data == "faq_centers":
        centers = "\n".join([f"• {c}" for c in CENTERS.keys()])
        response = f"{I['center']} *المراكز الطبية*\n\n{centers}"
    elif data == "faq_timing":
        response = f"{I['clock']} *مواعيد العيادات الخارجية*\n• السبت - الأربعاء: 8ص - 2م\n• الطوارئ: 24 ساعة"
    elif data == "faq_free":
        response = f"{I['success']} *الخدمات المجانية*\nنعم، يقدم المستشفى خدماته الطبية مجاناً للمرضى في معظم الأقسام."
    elif data == "faq_emergency":
        response = f"{I['emergency']} *الطوارئ*\n• يعمل 24 ساعة\n• 📞 {HOSPITAL['phone']}\n• 📍 {HOSPITAL['address']}"
    elif data == "faq_whatsapp":
        response = f"{I['whatsapp']} *واتساب مباشر*\n[اضغط هنا للتواصل]({SOCIAL_MEDIA['whatsapp_direct']})"
    elif data == "faq_media":
        media_links = f"{I['media']} *المركز الإعلامي*\n\n• تلغرام: [ALGUMHORI]({SOCIAL_MEDIA['telegram']})\n• فيسبوك: [GHTSMS]({SOCIAL_MEDIA['facebook_main']})\n• إكس: [@GHTSMS]({SOCIAL_MEDIA['x']})\n• انستجرام: [algumhori.ye]({SOCIAL_MEDIA['instagram']})\n• يوتيوب: [algumhori_live_ye]({SOCIAL_MEDIA['youtube']})"
        response = media_links
    
    await query.edit_message_text(response, parse_mode="Markdown", disable_web_page_preview=True)

async def hospital_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
{I['hospital']} *{HOSPITAL['full_name']}* {I['hospital']}

📖 *نبذة تعريفية:*
{HOSPITAL['description']}

📊 *إحصائيات:*
• 🛏️ السعة السريرية: {HOSPITAL['beds']}
• 💉 الخدمات: {HOSPITAL['services']}

📍 *العنوان:*
{HOSPITAL['address']}

📞 *للتواصل:*
{ HOSPITAL['phone'] }

⚕️ *الرؤية:* الريادة في تقديم الخدمات الصحية المجانية

💝 *الرسالة:* تقديم خدمات صحية مجانية بجودة عالية
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def doctors_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doctors_list = "\n".join([f"• *{title}:* {doc['name']}\n   📌 {doc['specialty']}" for title, doc in DOCTORS.items()])
    text = f"""
{I['doctor']} *الكوادر الطبية الرئيسية* {I['doctor']}

{doctors_list}

{I['info']} *للاستفسار عن مواعيد الأطباء:* 📞 {HOSPITAL['phone']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def departments_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    depts_list = "\n".join([f"• 🏥 {dept}" for dept in DEPARTMENTS.keys()])
    text = f"""
{I['department']} *الأقسام الطبية في المستشفى* {I['department']}

{depts_list}

📞 *للاستفسار:* {HOSPITAL['phone']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def centers_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    centers_list = "\n".join([f"• 🏛️ *{center}:* {desc}" for center, desc in CENTERS.items()])
    text = f"""
{I['center']} *المراكز الطبية المتخصصة* {I['center']}

{centers_list}

{I['info']} *جميع المراكز تقدم خدماتها مجاناً للمواطنين*
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def emergency_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
{I['emergency']} *حالة طارئة - تعليمات مهمة* {I['emergency']}

⚠️ *إذا كنت تعاني من أحد الأعراض التالية:*
• ألم شديد في الصدر
• صعوبة شديدة في التنفس
• فقدان الوعي
• نزيف حاد
• شلل مفاجئ

🚨 *اتصل فوراً:* `{HOSPITAL['phone']}`

📍 *العنوان:* {HOSPITAL['address']}

{I['warning']} *لا تنتظر - اذهب لأقرب طوارئ فوراً*
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
{I['phone']} *طرق التواصل مع المستشفى* {I['phone']}

📞 *الرقم الرئيسي:* `{HOSPITAL['phone']}`
📞 *الشكاوى:* `{HOSPITAL['complaints']}`
📧 *البريد:* `{HOSPITAL['email']}`

💬 *واتساب:* [تواصل مباشر]({SOCIAL_MEDIA['whatsapp_direct']})

🕐 *أوقات الاتصال:*
• الطوارئ: 24 ساعة
• الاستفسارات: 8ص - 8م
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def location_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
{I['location_pin']} *موقع هيئة المستشفى الجمهوري التعليمي* {I['location_pin']}

📍 *العنوان التفصيلي:*
{HOSPITAL['address']}

🗺️ *وسط العاصمة صنعاء - يسهل الوصول إليه*

📞 *للاستفسار عن الاتجاهات:* {HOSPITAL['phone']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def media_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
{I['media']} *المركز الإعلامي* {I['media']}

📺 *تابعونا على وسائل التواصل:*

{I['telegram']} *تلغرام:* [ALGUMHORI]({SOCIAL_MEDIA['telegram']})

{I['facebook']} *فيسبوك:* [GHTSMS]({SOCIAL_MEDIA['facebook_main']})

{I['twitter']} *إكس:* [@GHTSMS]({SOCIAL_MEDIA['x']})

{I['instagram']} *انستجرام:* [algumhori.ye]({SOCIAL_MEDIA['instagram']})

{I['youtube']} *يوتيوب:* [algumhori_live_ye]({SOCIAL_MEDIA['youtube']})

💬 *واتساب:* [تواصل مباشر]({SOCIAL_MEDIA['whatsapp_direct']})

---
📞 {HOSPITAL['phone']}
📍 {HOSPITAL['address']}
"""
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)

async def whatsapp_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
{I['whatsapp']} *تواصل مباشر عبر الواتساب* {I['whatsapp']}

📱 [اضغط هنا للتواصل]({SOCIAL_MEDIA['whatsapp_direct']})

💬 *يمكنك استخدام هذه الخدمة لـ:*
• حجز المواعيد
• الاستفسار عن الخدمات
• تقديم الملاحظات

📞 *أو اتصل على:* {HOSPITAL['phone']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def consultation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب استشارة وتوجيه"""
    await update.message.reply_text(
        f"{I['stethoscope']} *استشارة وتوجيه طبي* {I['stethoscope']}\n\n"
        f"📝 *صف أعراضك بالتفصيل:*\n"
        f"• مكان الألم أو المشكلة\n"
        f"• متى بدأت\n"
        f"• شدتها (خفيفة/متوسطة/شديدة)\n\n"
        f"📝 *مثال:* 'عندي ألم في صدري من 3 أيام'\n"
        f"📝 *مثال:* 'طفلي عنده حرارة 39 ويسعل'\n\n"
        f"{I['info']} *سأقوم بتوجيهك للقسم الطبي المناسب*",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل"""
    msg = update.message.text
    
    # الأزرار الرئيسية
    if msg == f"{I['question']} أسئلة شائعة":
        await faq_handler(update, context)
    elif msg == f"{I['stethoscope']} استشارة وتوجيه":
        await consultation_handler(update, context)
    elif msg == f"{I['hospital']} معلومات المستشفى":
        await hospital_info(update, context)
    elif msg == f"{I['doctor']} الكوادر الطبية":
        await doctors_info(update, context)
    elif msg == f"{I['department']} الأقسام":
        await departments_info(update, context)
    elif msg == f"{I['center']} المراكز":
        await centers_info(update, context)
    elif msg == f"{I['emergency']} طوارئ":
        await emergency_handler(update, context)
    elif msg == f"{I['phone']} التواصل":
        await contact_info(update, context)
    elif msg == f"{I['location']} الموقع":
        await location_info(update, context)
    elif msg == f"{I['media']} المركز الإعلامي":
        await media_center(update, context)
    elif msg == f"{I['whatsapp']} واتساب مباشر":
        await whatsapp_direct(update, context)
    else:
        # البحث عن إجابة
        answer = find_answer(msg)
        
        if answer:
            await update.message.reply_text(answer, parse_mode="Markdown")
            return
        
        # توجيه المريض حسب الأعراض
        department = find_department(msg)
        
        if department:
            response = f"""
{I['stethoscope']} *توجيه طبي*

بناءً على الأعراض التي ذكرتها:

{department}

📞 *للاستفسار أو الحجز:* {HOSPITAL['phone']}
📍 *العنوان:* {HOSPITAL['address']}

{I['warning']} هذا توجيه أولي، يُفضل مراجعة الطبيب المختص لتشخيص دقيق
"""
            await update.message.reply_text(response, parse_mode="Markdown")
        else:
            response = f"""
{I['info']} *لم أستطع فهم سؤالك بالكامل*

يمكنك:
• استخدام الأزرار أعلاه للحصول على معلومات مباشرة
• إعادة صياغة السؤال بشكل أوضح
• الاتصال على الرقم {HOSPITAL['phone']} للاستفسار

📝 *أمثلة لأسئلة يمكنك طرحها:*
• أين يقع المستشفى؟
• ما هي الأقسام الطبية؟
• رقم الطوارئ؟
• عندي ألم في بطني - أي قسم أروح؟

{I['stethoscope']} أو صف أعراضك وسأوجهك للقسم المناسب
"""
            await update.message.reply_text(response, parse_mode="Markdown")

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
        "status": "✅ بوت هيئة المستشفى الجمهوري التعليمي شغال",
        "bot": "@Hospitalalg_bot",
        "name": HOSPITAL['full_name'],
        "version": "FAQ & Guidance System v1.0",
        "features": ["أسئلة شائعة", "توجيه المرضى", "معلومات المستشفى", "الكوادر الطبية", "المركز الإعلامي"]
    })

@app.route('/webhook', methods=['POST'])
async def webhook():
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
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"🚀 تشغيل بوت هيئة المستشفى الجمهوري التعليمي...")
    logger.info(f"📍 Port: {port}")
    logger.info(f"📱 Bot: @Hospitalalg_bot")
    logger.info(f"📊 FAQ Database: {len(FAQ_DATABASE)} سؤال")
    logger.info(f"🏥 Departments: {len(DEPARTMENTS)} قسم")
    
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    run_webhook_mode()
