import os
import telebot
from flask import Flask, request
import google.generativeai as genai

TOKEN = "8628230178:AAFgYbbGxdQZiIbQBPBkcunBTlIcpqFPfHQ"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
ADMIN_ID = 8345712050

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

bot_active = True 
user_chat_sessions = {}
all_users = set()

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
    btn_stats = telebot.types.InlineKeyboardButton(
        f"👥 Total Users: {len(all_users)}", 
        callback_data="stats_users"
    )
    btn_broadcast = telebot.types.InlineKeyboardButton(
        "📢 Broadcast Message", 
        callback_data="broadcast_prompt"
    )

    markup.add(btn_status)
    markup.add(btn_stats)
    markup.add(btn_broadcast)

    bot.send_message(message.chat.id, "👑 অ্যাডমিন কন্ট্রোল প্যানেল:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["toggle_bot", "stats_users", "broadcast_prompt"])
def admin_callbacks(call):
    global bot_active
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "আপনার অনুমতি নেই!", show_alert=True)
        return

    if call.data == "toggle_bot":
        bot_active = not bot_active
        status_text = "ON ✅" if bot_active else "OFF ❌"

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(f"🤖 Bot: {status_text}", callback_data="toggle_bot"))
        markup.add(telebot.types.InlineKeyboardButton(f"👥 Total Users: {len(all_users)}", callback_data="stats_users"))
        markup.add(telebot.types.InlineKeyboardButton("📢 Broadcast Message", callback_data="broadcast_prompt"))

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id, f"বটের স্ট্যাটাস পরিবর্তন করে করা হয়েছে: {status_text}")

    elif call.data == "stats_users":
        bot.answer_callback_query(call.id, f"মোট ইউনিক ব্যবহারকারী: {len(all_users)} জন", show_alert=True)

    elif call.data == "broadcast_prompt":
        msg = bot.send_message(call.message.chat.id, "📢 আপনি সকল ইউজারের কাছে যে মেসেজটি পাঠাতে চান সেটি লিখুন:")
        bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return

    broadcast_text = message.text
    success_count = 0
    fail_count = 0

    bot.reply_to(message, "⏳ ব্রডকাস্ট মেসেজ পাঠানো হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")

    for uid in all_users:
        try:
            bot.send_message(uid, f"📢 **অ্যাডমিনের ঘোষণা:**\n\n{broadcast_text}", parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            fail_count += 1

    bot.send_message(ADMIN_ID, f"✅ ব্রডকাস্ট সম্পন্ন!\nসফল: {success_count} জন\nব্যর্থ: {fail_count} জন")

# টেলিগ্রাম বিজনেস মেসেজ হ্যান্ডলার
@bot.business_message_handler(func=lambda message: True)
def handle_business_message(message):
    global bot_active

    if not bot_active:
        return

    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        all_users.add(user_id)

    user_text = message.text
    if not user_text:
        return

    try:
        if user_id not in user_chat_sessions:
            user_chat_sessions[user_id] = model.start_chat(history=[])

        chat = user_chat_sessions[user_id]
        response = chat.send_message(user_text)

        bot.send_message(
            chat_id=message.chat.id, 
            text=response.text, 
            business_connection_id=message.business_connection_id
        )
    except Exception as e:
        print(f"Business AI Error: {e}")

# নরমাল চ্যাট হ্যান্ডলার
@bot.message_handler(func=lambda message: True)
def handle_normal_message(message):
    global bot_active

    if not bot_active:
        return

    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        all_users.add(user_id)

    user_text = message.text
    if not user_text:
        return

    try:
        if user_id not in user_chat_sessions:
            user_chat_sessions[user_id] = model.start_chat(history=[])

        chat = user_chat_sessions[user_id]
        response = chat.send_message(user_text)
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Normal Error: {e}")

# ফ্লাস্কের মাধ্যমে ওয়েব হুক রাউট সেটআপ
@server.route(f"/{TOKEN}", methods=["POST"])
def redirect_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    else:
        return "Invalid Data", 403

@server.route("/")
def index():
    return "Bot is running smoothly with Webhook!", 200

if __name__ == "__main__":
    # আপনার রেন্ডার অ্যাপের মূল ইউআরএল এখানে বসাতে হবে (যেমন: https://your-app-name.onrender.com)
    # রেন্ডারে ডিপ্লয় করার পর রেন্ডারের দেওয়া প্রোজেক্ট লিংকটি এখানে দিয়ে দেবেন অথবা নিচে অটো সেটআপ কোড ব্যবহার করতে পারেন:
    
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}", allowed_updates=['message', 'business_message', 'callback_query', 'business_connection'])

    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
