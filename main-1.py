import os
import telebot
import google.generativeai as genai

TOKEN = "8856458972:AAFHuTmDM0TtvM21J1-KhEse3m71nIf8LG8"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyD_S9lsn1ULXCuqs2yyjpNxlbKq2DU9QOo")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_message = message.text
    try:
        response = model.generate_content(user_message)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "দুঃখিত, এই মুহূর্তে উত্তর দিতে পারছি না।")

print("টেলিগ্রাম এআই বট অনলাইনে সচল রয়েছে...")
bot.infinity_polling()
