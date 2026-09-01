import os
import telebot
from flask import Flask, request
import google.generativeai as genai

TOKEN = "8628230178:AAGfzaIXjypbb8bk0Vog69lSwi8_7YO5VSs"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
ADMIN_ID = 8345712050

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-3.7-flash")


bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

bot_active = True 
user_chat_sessions = {}

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "দুঃখিত, এই কমান্ডটি শুধুমাত্র আপনার (অ্যাডমিনের) জন্য নির্ধারিত।")
        return

    markup = telebot.types.InlineKeyboardMarkup()
    btn_status = telebot.types.InlineKeyboardButton(
        f"🤖 Bot: {'ON ✅' if bot_active else 'OFF ❌'}", 
        callback_data="toggle_bot"
    )
    markup.add(btn_status)
    bot.send_message(message.chat.id, "অ্যাডমিন কন্ট্রোল প্যানেল:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_bot")
def toggle_bot_callback(call):
    global bot_active
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "আপনার অনুমতি নেই!", show_alert=True)
        return

    bot_active = not bot_active
    status_text = "ON ✅" if bot_active else "OFF ❌"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(f"🤖 Bot: {status_text}", callback_data="toggle_bot"))

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, f"বটের স্ট্যাটাস পরিবর্তন করে করা হয়েছে: {status_text}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global bot_active
    if not bot_active and message.from_user.id != ADMIN_ID:
        return

    user_id = message.from_user.id
    user_text = message.text

    try:
        if user_id not in user_chat_sessions:
            user_chat_sessions[user_id] = model.start_chat(history=[])

        chat = user_chat_sessions[user_id]
        response = chat.send_message(user_text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"দুঃখিত, একটি সমস্যা হয়েছে: {str(e)}")

@server.route("/")
def index():
    return "Bot is running smoothly!", 200

import threading

def run_bot():
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f"Polling error: {e}")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
