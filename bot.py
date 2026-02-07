import telebot
import google.generativeai as genai
from telebot import types
import os
from PIL import Image
import qrcode

# --- البيانات ---
TOKEN = "8338508591:AAEpGjSi7XTh_jV3nqa0HWKIanpjNEp3Ey0"
GEMINI_KEY = "AIzaSyDWpI20pIP-TqtfxCljfL4eQRR2Vx6BSb8"

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)

# --- البحث عن الموديل الشغال (نفس طريقتك الأصلية) ---
available_model = None
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_model = m.name
            break
except: pass
if not available_model: available_model = 'models/gemini-1.5-flash'

model = genai.GenerativeModel(available_model)

# --- دالة الزخرفة ---
def get_all_decorations(name):
    n = name.upper()
    styles = [
        "".join([chr(ord(c) + 120211) if 'A' <= c <= 'Z' else c for c in n]),
        "".join([chr(ord(c) + 120263) if 'A' <= c <= 'Z' else c for c in n]),
        "".join([chr(ord(c) + 120419) if 'A' <= c <= 'Z' else c for c in n]),
        "".join([chr(ord(c) + 120315) if 'A' <= c <= 'Z' else c for c in n]),
        "".join([chr(ord(c) + 120367) if 'A' <= c <= 'Z' else c for c in n]),
        n,
        f"⚡ {n} ⚡", f"『ツ』☆{n}", f"꧁ {n} ꧂", f"♛ {n} ♛", f"✨ {n} ✨"
    ]
    return styles

# --- القائمة الشيك (خانات طويلة وكبيرة) ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✉️ كاتب إيميلات إحترافي", callback_data="email"),
        types.InlineKeyboardButton("🔍 محقق رقمي (OSINT)", callback_data="osint"),
        types.InlineKeyboardButton("📱 استخبارات تيك توك (TikTok)", callback_data="tiktok"),
        types.InlineKeyboardButton("🕵️ فحص الصور وكشف التزييف", callback_data="photo"),
        types.InlineKeyboardButton("🖼️ إنشاء QR Code سريع", callback_data="make_qr"),
        types.InlineKeyboardButton("🎥 تحميل غلاف يوتيوب HD", callback_data="yt_thumb"),
        types.InlineKeyboardButton("✨ زخرفة الأسماء (أشكال مميزة)", callback_data="decorate")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Welcome! 🚀\nاختر الميزة التي تريدها من الأزرار أدناه:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "email":
        msg = bot.send_message(call.message.chat.id, "✍️ أرسل موضوع الإيميل:")
        bot.register_next_step_handler(msg, call_ai, "اكتب إيميل رسمي عن: ")
    elif call.data == "osint":
        msg = bot.send_message(call.message.chat.id, "🔎 أرسل اليوزر نيم للبحث عنه:")
        bot.register_next_step_handler(msg, call_ai, "ابحث عن روابط السوشيال ميديا لليوزر: ")
    elif call.data == "photo":
        bot.send_message(call.message.chat.id, "📸 ارفع الصورة دلوقتي عشان أحللها لك...")
    elif call.data == "make_qr":
        msg = bot.send_message(call.message.chat.id, "🔗 أرسل الرابط لصنع QR Code:")
        bot.register_next_step_handler(msg, generate_qr)
    elif call.data == "yt_thumb":
        msg = bot.send_message(call.message.chat.id, "🎥 أرسل رابط فيديو اليوتيوب:")
        bot.register_next_step_handler(msg, get_youtube_thumb)
    elif call.data == "decorate":
        msg = bot.send_message(call.message.chat.id, "✨ أرسل الاسم المراد زخرفته:")
        bot.register_next_step_handler(msg, handle_decoration_step)
    elif call.data == "tiktok":
        msg = bot.send_message(call.message.chat.id, "📱 أرسل يوزر حساب التيك توك (بدون @):")
        bot.register_next_step_handler(msg, handle_tiktok_osint)

# --- تصليح ميزة تحليل الصور (رجوع للأصل الشغال) ---
@bot.message_handler(content_types=['photo'])
def handle_photo_upload(message):
    bot.send_message(message.chat.id, "⏳ جاري فحص الصورة بأعلى دقة...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        with open("analyzed_img.jpg", "wb") as f: f.write(downloaded)
        
        # الكود الأصلي للتحليل
        img = Image.open("analyzed_img.jpg")
        response = model.generate_content(["حلل الصورة دي وكشف التزييف فيها بالتفصيل:", img])
        
        bot.send_message(message.chat.id, f"🔍 نتيجة التحليل:\n\n{response.text}", reply_markup=main_menu())
        os.remove("analyzed_img.jpg")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل التحليل: {e}", reply_markup=main_menu())

# --- باقي الوظائف ---
def handle_tiktok_osint(message):
    bot.send_message(message.chat.id, "⏳ جاري سحب بيانات تيك توك...")
    prompt = f"قم بعمل OSINT كامل لحساب تيك توك باسم {message.text}. استخرج تاريخ الإنشاء، الدولة، نوع الحساب، والتحليلات المتاحة."
    try:
        res = model.generate_content(prompt)
        bot.send_message(message.chat.id, f"📊 تقرير الحساب:\n\n{res.text}", reply_markup=main_menu())
    except: bot.send_message(message.chat.id, "❌ خطأ في البيانات.", reply_markup=main_menu())

def handle_decoration_step(message):
    bot.send_message(message.chat.id, "⏳ جاري الزخرفة...")
    styles = get_all_decorations(message.text)
    for s in styles: bot.send_message(message.chat.id, s)
    bot.send_message(message.chat.id, "✅ تم!", reply_markup=main_menu())

def generate_qr(message):
    try:
        img = qrcode.make(message.text)
        img.save("qr.png")
        with open("qr.png", "rb") as f: bot.send_photo(message.chat.id, f)
        os.remove("qr.png")
    except: bot.send_message(message.chat.id, "❌ فشل.")
    bot.send_message(message.chat.id, "تمت المهمة!", reply_markup=main_menu())

def get_youtube_thumb(message):
    try:
        url = message.text
        v_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1].split("?")[0]
        bot.send_photo(message.chat.id, f"https://img.youtube.com/vi/{v_id}/maxresdefault.jpg")
    except: bot.send_message(message.chat.id, "❌ رابط خطأ.")
    bot.send_message(message.chat.id, "تمت المهمة!", reply_markup=main_menu())

def call_ai(message, prompt_text):
    bot.send_message(message.chat.id, "⏳ جاري المعالجة...")
    try:
        response = model.generate_content(prompt_text + message.text)
        bot.send_message(message.chat.id, f"📝 النتيجة:\n\n{response.text}", reply_markup=main_menu())
    except Exception as e: bot.send_message(message.chat.id, f"❌ خطأ: {e}", reply_markup=main_menu())

print("🚀 البوت شغال والتحليل رجع زي الأول وأحسن!")
bot.infinity_polling()
