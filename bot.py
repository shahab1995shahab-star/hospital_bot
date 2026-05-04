import os
import json
import asyncio
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify
import threading

# ========== التوكنات والمفاتيح ==========
TELEGRAM_TOKEN = "8743390722:AAHLDi36JpRC5AJabXPTA6yzERK6MdVTo6c"
GEMINI_API_KEY = "AIzaSyCWDo3VlPLsTPs5b4zKNzHAmdSC8U29Rsw"  # 🔑 حط المفتاح اللي حفظته هنا

# ========== تشغيل Gemini ==========
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ========== معلومات المستشفى ==========
HOSPITAL_INFO = {
    "name": "مستشفى الجمهوري التعليمي - صنعاء",
    "address": "شارع إسماعيل هنية (الزبيري سابقاً) - أمانة العاصمة",
    "phone": "781695995",
    "complaints_phone": "779157779",
    "email": "info@algumhorihosp-san.gov.ye",
    "whatsapp": "https://whatsapp.com/channel/0029Va8kJ8e2Jl8DAoEmbM0v",
    "beds": "650 سرير",
    "description": "أقدم المستشفيات الحكومية في صنعاء، يقدم خدماته الصحية مجاناً لمئات الآلاف يومياً بكادر طبي يمني مؤهل وأجهزة حديثة"
}

# ========== الأقسام الطبية ==========
DEPARTMENTS = {
    "العظام والمفاصل": ["كسر", "عظم", "مفصل", "ظهر", "ركبة", "كتف", "يد", "رجل", "الديسك"],
    "المخ والأعصاب": ["صداع", "شقيقة", "دوار", "صرع", "تشنج", "تنميل", "شلل"],
    "الجراحة العامة": ["فتق", "زائدة", "مرارة", "استئصال", "ورم", "جرح"],
    "المسالك البولية": ["بول", "كلية", "حصوة", "تبول", "بروستاتا"],
    "الأنف والأذن والحنجرة": ["أذن", "أنف", "حنجرة", "سمع", "لوز"],
    "الباطنية": ["ضغط", "سكر", "قلب", "صدر", "كبد", "معده", "قولون", "اسهال", "امساك", "حمى"],
    "الأطفال": ["طفل", "رضيع", "صغير", "حضانة", "تطعيم"],
    "العيون": ["عين", "بصر", "نظر", "رمد"],
    "الجلدية": ["جلد", "حكة", "طفح", "حساسية", "صدفية"],
    "الطوارئ العامة": ["طوارئ", "اسعاف", "حادث", "اصابة", "نزيف"]
}

# ========== الكوادر الطبية ==========
DOCTORS = {
    "رئيس الهيئة": "أ.د. محمد طاهر جحاف - استشاري العظام والمفاصل",
    "نائب رئيس الهيئة للشؤون الفنية": "د.عمار قداري - رئيس قسم الجراحة",
    "نائب رئيس الهيئة للشؤون السريرية": "د.نبيل الحاج - اخصائي جراحة وأورام",
    "نائب رئيس الهيئة للشؤون الأكاديمية": "أ.د.محمد البعداني - طب عام وجراحة",
    "رئيس قسم العظام": "د/معتز الصنوي",
    "رئيس قسم الجراحة العامة": "د/عبدالله الاشول",
    "رئيس قسم الباطنية": "د/عبد الواسع مجاهد",
    "رئيس قسم الأطفال والحضانة": "د/ناشر الاغبري",
    "مدير مركز الطوارئ العامة": "د/ياسر البريهي"
}

# ========== دالة الذكاء الاصطناعي Gemini ==========
async def get_ai_response(user_message):
    try:
        prompt = f"""
أنت مساعد طبي ذكي لمستشفى الجمهوري التعليمي في صنعاء.

معلومات عن المستشفى:
- الاسم: {HOSPITAL_INFO['name']}
- العنوان: {HOSPITAL_INFO['address']}
- رقم الطوارئ: {HOSPITAL_INFO['phone']}
- الأقسام المتوفرة: {', '.join(DEPARTMENTS.keys())}

تعليمات مهمة للرد:
1. حلل الأعراض التي ذكرها المريض بطريقة مهنية ودقيقة
2. اقترح القسم المناسب للمراجعة من الأقسام المتوفرة
3. إذا كانت الأعراض خطيرة (ألم صدر، صعوبة تنفس، نزيف حاد، فقدان وعي) قول "🚨 حالة طارئة - توجه فوراً للطوارئ"
4. لا تقدم تشخيصاً قطعياً، استخدم عبارات مثل "بناءً على الأعراض المذكورة..."
5. أضف دائماً "⚠️ هذا ليس بديلاً عن استشارة الطبيب المختص"
6. إذا السؤال مو طبي (رياضة، طبخ، فيلم) جاوب بشكل عام ومختصر
7. إذا السؤال عن مواعيد أو معلومات إدارية، استخدم معلومات المستشفى أعلاه

سؤال المريض: "{user_message}"

الرد:
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"خطأ في Gemini: {e}")
        return None

# ========== تحديد القسم حسب الأعراض (بدون AI) ==========
def find_department(symptoms):
    symptoms_lower = symptoms.lower()
    for dept, keywords in DEPARTMENTS.items():
        for keyword in keywords:
            if keyword in symptoms_lower:
                return dept
    return None

# ========== دوال البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("🏥 معلومات المستشفى"), KeyboardButton("📋 الأقسام الطبية")],
        [KeyboardButton("👨‍⚕️ الكوادر الطبية"), KeyboardButton("🔍 استشارة طبية")],
        [KeyboardButton("📍 الموقع"), KeyboardButton("📞 أرقام مهمة")],
        [KeyboardButton("🆘 شكوى"), KeyboardButton("💬 واتساب")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🏥 **مرحباً بك في بوت مستشفى الجمهوري التعليمي - صنعاء** 🏥\n\n"
        "أنا مساعدك الذكي المدعوم بالذكاء الاصطناعي Gemini 🤖\n\n"
        "يمكنك:\n"
        "✅ كتابة الأعراض بالعامية أو الفصحى وسأحللها لك\n"
        "✅ سؤال أي استفسار طبي أو إداري\n"
        "✅ اختيار أحد الأزرار أدناه للمعلومات السريعة\n\n"
        f"📞 للطوارئ: {HOSPITAL_INFO['phone']}\n\n"
        "⚠️ ملاحظة: أنا للمساعدة الأولية فقط، وليس بديلاً عن زيارة الطبيب",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def hospital_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"🏥 **{HOSPITAL_INFO['name']}**\n\n" \
           f"📖 {HOSPITAL_INFO['description']}\n\n" \
           f"📍 **العنوان:** {HOSPITAL_INFO['address']}\n" \
           f"🛏️ **السعة السريرية:** {HOSPITAL_INFO['beds']}\n\n" \
           f"📞 **للتواصل:** {HOSPITAL_INFO['phone']}"
    await update.message.reply_text(text, parse_mode="Markdown")

async def departments_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    depts_list = "\n".join([f"• {dept}" for dept in DEPARTMENTS.keys()])
    text = f"🏥 **الأقسام الطبية:**\n\n{depts_list}"
    await update.message.reply_text(text, parse_mode="Markdown")

async def doctors_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doctors_list = "\n".join([f"• **{title}:** {name}" for title, name in DOCTORS.items()])
    text = f"👨‍⚕️ **الكوادر الطبية:**\n\n{doctors_list}"
    await update.message.reply_text(text, parse_mode="Markdown")

async def medical_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **الاستشارة الطبية بالذكاء الاصطناعي Gemini**\n\n"
        "أخبرني بالأعراض التي تعاني منها بأي لغة وبأي طريقة، وسأقوم بـ:\n\n"
        "🔍 تحليل الأعراض\n"
        "🏥 اقتراح القسم المناسب\n"
        "💊 نصائح أولية\n"
        "🚨 تحديد الحالات الخطيرة\n\n"
        "📝 **مثال:** 'عندي صداع شديد ودوخة من يومين مع حرارة'\n"
        "📝 **مثال:** 'ألم في البطن مع غثيان وإسهال'\n\n"
        "⚠️ ملاحظة: هذا ليس تشخيصاً طبياً بديلاً عن زيارة الطبيب"
    )

async def important_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"📞 **أرقام مهمة:**\n\n" \
           f"• **للطوارئ والاستفسار:** {HOSPITAL_INFO['phone']}\n" \
           f"• **للشكاوى:** {HOSPITAL_INFO['complaints_phone']}\n" \
           f"• **البريد الإلكتروني:** {HOSPITAL_INFO['email']}"
    await update.message.reply_text(text, parse_mode="Markdown")

async def location_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"📍 **موقع المستشفى:**\n\n{HOSPITAL_INFO['address']}"
    await update.message.reply_text(text)

async def complaint_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"🆘 **تقديم شكوى**\n\n" \
           f"يرجى التواصل على الرقم المخصص:\n\n" \
           f"📞 **{HOSPITAL_INFO['complaints_phone']}**"
    await update.message.reply_text(text)

async def whatsapp_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"💬 **قناة واتساب:**\n\n{HOSPITAL_INFO['whatsapp']}"
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # الأزرار المحددة
    if user_message == "🏥 معلومات المستشفى":
        await hospital_info(update, context)
    elif user_message == "📋 الأقسام الطبية":
        await departments_info(update, context)
    elif user_message == "👨‍⚕️ الكوادر الطبية":
        await doctors_info(update, context)
    elif user_message == "🔍 استشارة طبية":
        await medical_consultation(update, context)
    elif user_message == "📞 أرقام مهمة":
        await important_numbers(update, context)
    elif user_message == "📍 الموقع":
        await location_info(update, context)
    elif user_message == "🆘 شكوى":
        await complaint_info(update, context)
    elif user_message == "💬 واتساب":
        await whatsapp_info(update, context)
    else:
        # إرسال "يتم الرد..." لتجنب انتظار المستخدم
        await update.message.reply_text("🤖 **جاري تحليل سؤالك...** يرجى الانتظار لحظات", parse_mode="Markdown")
        
        # محاولة الحصول على رد من الذكاء الاصطناعي
        ai_response = await get_ai_response(user_message)
        
        if ai_response:
            await update.message.reply_text(ai_response, parse_mode="Markdown")
        else:
            # إذا فشل AI، نستخدم الطريقة العادية
            emergency_words = ["نزيف حاد", "فقد وعي", "لا يتنفس", "نوبة قلبية", "سكتة"]
            if any(word in user_message.lower() for word in emergency_words):
                await update.message.reply_text(
                    f"🚨 **حالة طارئة!** 🚨\n\n"
                    f"يرجى التوجه فوراً لقسم الطوارئ\n"
                    f"📞 الاتصال: {HOSPITAL_INFO['phone']}\n"
                    f"📍 {HOSPITAL_INFO['address']}",
                    parse_mode="Markdown"
                )
                return
            
            dept = find_department(user_message)
            if dept:
                await update.message.reply_text(
                    f"📋 **بناءً على الأعراض، ننصحك بمراجعة قسم:**\n\n"
                    f"🏥 **{dept}**\n\n"
                    f"📍 مستشفى الجمهوري التعليمي\n"
                    f"📞 للاستفسار: {HOSPITAL_INFO['phone']}\n\n"
                    f"⚠️ هذا ليس بديلاً عن استشارة الطبيب",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "🙏 **لم أتمكن من تحليل سؤالك حالياً**\n\n"
                    f"يمكنك:\n"
                    f"1️⃣ الاتصال على الرقم {HOSPITAL_INFO['phone']} للحصول على المساعدة\n"
                    f"2️⃣ إعادة كتابة السؤال بشكل أوضح\n"
                    f"3️⃣ استخدام الأزرار أعلاه للحصول على معلومات مباشرة\n\n"
                    f"📝 مثال لكتابة الأعراض: 'أعاني من ألم في المعدة وإسهال مستمر'"
                )

# ========== إعداد Flask لـ Webhook ==========
app = Flask(__name__)
telegram_app = None

@app.route('/')
def home():
    return jsonify({"status": "بوت مستشفى الجمهوري التعليمي شغال ✅", "bot": "@Hospitalalg_bot", "ai": "Google Gemini 🤖"})

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
    return jsonify({"status": "healthy"}), 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ========== تشغيل البوت ==========
def main():
    global telegram_app
    
    # إنشاء تطبيق البوت
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # بدء Flask في خيط منفصل
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    print("✅ Flask server شغال...")
    
    # تشغيل polling
    print("✅ بوت مستشفى الجمهوري التعليمي مع Gemini AI شغال...")
    telegram_app.run_polling()

if __name__ == '__main__':
    main()