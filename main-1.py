import os
import telebot
import google.generativeai as genai

# আপনার ক্রেডেনশিয়াল এবং অ্যাডমিন আইডি
TOKEN = "8856458972:AAFHuTmDM0TtvM21J1-KhEse3m71nIf8LG8"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyD_S9lsn1ULXCuqs2yyjpNxlbKq2DU9QOo")
ADMIN_ID = 8345712050  # আপনার নির্দিষ্ট টেলিগ্রাম আইডি

genai.configure(api_key=GEMINI_API_KEY)
# চ্যাট হিস্ট্রি বা কনটেক্সট মেমোরি বজায় রাখার জন্য GenerativeModel-এর পরিবর্তে chat session ব্যবহার করা ভালো
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(TOKEN)

# বটের কন্ট্রোল স্ট্যাটাস ভেরিয়েবল
bot_active = True  # বট অন বা অফ রাখার জন্য
user_chat_sessions = {} # ইউজারের সাথে কনভার্সেশন হিস্ট্রি ধরে রাখার ডিকশনারি

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "দুঃখিত, এই কমান্ডটি শুধুমাত্র আপনার (অ্যাডমিনের) জন্য নির্ধারিত।")
        return
    
    markup = telebot.types.InlineKeyboardMarkup()
    btn_on = telebot.types.InlineKeyboardButton("🟢 বট চালু করুন", callback_data="bot_on")
    btn_off = telebot.types.InlineKeyboardButton("🔴 বট বন্ধ রাখুন", callback_data="bot_off")
    markup.add(btn_on, btn_off)
    
    status_text = "সচল (Active)" if bot_active else "বন্ধ (Paused)"
    bot.reply_to(message, f"⚙️ **পার্সোনাল অ্যাডমিন কন্ট্রোল প্যানেল**\n\nবটের বর্তমান অবস্থা: *{status_text}*\nনিচের বাটন থেকে নিয়ন্ত্রণ করুন:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global bot_active
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "আপনার অনুমতি নেই!")
        return
    
    if call.data == "bot_on":
        bot_active = True
        bot.edit_message_text("🟢 বট সফলভাবে চালু করা হয়েছে!", call.message.chat.id, call.message.message_id)
    elif call.data == "bot_off":
        bot_active = False
        bot.edit_message_text("🔴 বট সাময়িকভাবে বন্ধ রাখা হয়েছে।", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global bot_active
    
    # বট বন্ধ থাকলে কোনো কাজ করবে না
    if not bot_active:
        return  
        
    # আপনি নিজে যদি চ্যাটে কথা বলেন বা কোনো কমান্ড দেন, তবে বট আপনার মেসেজে নিজে থেকে এআই রিপ্লাই দিয়ে ডিস্টার্ব করবে না
    if message.from_user.id == ADMIN_ID:
        if message.text and message.text.startswith("/"):
            return # কমান্ড হলে স্কিপ করবে
        # আপনি নিজে একটিভ থাকলে বট সাইলেন্ট থাকবে (অটো রেসপন্স সাপ্রেশন)
        return

    user_id = message.from_user.id
    user_message = message.text

    if not user_message:
        return

    try:
        # প্রতিটা ইউজারের জন্য আলাদা চ্যাট সেশন বা মেমোরি তৈরি করা যাতে আগের কথা মনে রাখতে পারে
        if user_id not in user_chat_sessions:
            user_chat_sessions[user_id] = model.start_chat(history=[])
        
        chat_session = user_chat_sessions[user_id]
        response = chat_session.send_message(user_message)
        
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "দুঃখিত, এই মুহূর্তে উত্তর দিতে পারছি না।")

print("পার্সোনাল অ্যাসিস্ট্যান্ট বট অ্যাডমিন প্যানেল ও মেমোরিসহ সচল রয়েছে...")
bot.infinity_polling()
