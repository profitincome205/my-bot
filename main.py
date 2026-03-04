import telebot
from telebot import types

# --- Pengaturan Bot ---
API_TOKEN = '7760979122:AAFyxBtoBtzU5wLreLl9jfUurlimtDGhKIY' 
ADMIN_ID = 8290768037  
MIN_DEPOSIT = 10.0
USDT_ADDRESS = "0xa40e6b91cf5a1810ef0b118f32f44330cb820ab3"

bot = telebot.TeleBot(API_TOKEN)

# Database Sementara (Simulasi)
user_balances = {} 

def get_user_balance(user_id):
    return user_balances.get(user_id, 0.0)

# --- Menu Utama ---
def main_menu(chat_id, user_id):
    balance = get_user_balance(user_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton("Sell Account", callback_data="sell_acc")
    btn2 = types.InlineKeyboardButton("Buy Account", callback_data="buy_acc")
    btn3 = types.InlineKeyboardButton("TopUp Balance", callback_data="topup")
    btn4 = types.InlineKeyboardButton("Payout Money", callback_data="payout")
    btn5 = types.InlineKeyboardButton("More", callback_data="more")
    btn6 = types.InlineKeyboardButton("Back", callback_data="main_menu")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    text = f"Your account ID: {user_id}\nTotal balance: {balance}$"
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    main_menu(message.chat.id, message.from_user.id)

# --- Callback Handler ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    if call.data == "main_menu":
        main_menu(call.message.chat.id, user_id)

    # --- Bagian TopUp (Deposit) ---
    elif call.data == "topup":
        msg = bot.edit_message_text(
            f"💳 **Minimum Deposit: {MIN_DEPOSIT}$**\n\nSilakan masukkan jumlah yang ingin Anda depositkan:",
            call.message.chat.id, call.message.message_id, parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_deposit_amount)

    # --- Bagian Jual Akun ---
    elif call.data == "sell_acc":
        markup = types.InlineKeyboardMarkup()
        btn_price = types.InlineKeyboardButton("⌕ Prices", callback_data="view_prices")
        markup.add(btn_price)
        bot.edit_message_text("Send phone number ⌕ Prices", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "view_prices":
        price_list = "🇺🇿]+998–UZ: 0.60$\n[🇧🇩]+880–BD: 0.20$\n[🇺🇸]+1–US: 0.20$\nNumber No Need"
        bot.answer_callback_query(call.id, text=price_list, show_alert=True)

    # --- Bagian Beli Akun ---
    elif call.data == "buy_acc":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("Server (1)", callback_data="server1"),
                   types.InlineKeyboardButton("Server (2)", callback_data="server2"),
                   types.InlineKeyboardButton("Back", callback_data="main_menu"))
        text = f"🎲 Buy Ready Telegram Accounts:\n––––––—————\n• Total balance = {get_user_balance(user_id)}$"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    # --- Aksi Admin (Setujui/Tolak) ---
    elif call.data.startswith(("app_", "rej_")):
        if user_id != ADMIN_ID: return
        
        data = call.data.split("_")
        action = data[0]
        target_uid = int(data[1])
        
        if action == "app":
            amount = float(data[2])
            user_balances[target_uid] = user_balances.get(target_uid, 0.0) + amount
            bot.send_message(target_uid, f"✅ Deposit Anda sebesar {amount}$ telah disetujui!")
            bot.edit_message_text(f"✅ Disetujui {amount}$ untuk User {target_uid}", ADMIN_ID, call.message.message_id)
        else:
            bot.send_message(target_uid, "❌ Permintaan deposit Anda ditolak oleh admin.")
            bot.edit_message_text(f"❌ Ditolak untuk User {target_uid}", ADMIN_ID, call.message.message_id)

# --- Fungsi Proses Deposit ---
def process_deposit_amount(message):
    try:
        amount = float(message.text)
        if amount < MIN_DEPOSIT:
            bot.reply_to(message, f"❌ Error: Minimum deposit adalah {MIN_DEPOSIT}$.\nKetik /start untuk mencoba lagi.")
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Saya sudah bayar (Kirim Bukti)", callback_data=f"paid_{amount}"))
        
        text = (
            f"✅ Jumlah: {amount}$\n\n"
            f"Kirim pembayaran ke:\n`{USDT_ADDRESS}`\n"
            f"Network: **USDT BEP20**\n\n"
            "Setelah melakukan pembayaran, klik tombol di bawah untuk mengirim bukti (Screenshot/Hash)."
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
    except:
        bot.reply_to(message, "❌ Jumlah tidak valid. Gunakan angka saja.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def submit_proof(call):
    amount = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, "Silakan kirim Transaction Hash atau Screenshot pembayaran:")
    bot.register_next_step_handler(msg, send_to_admin, amount)

def send_to_admin(message, amount):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Setujui", callback_data=f"app_{user_id}_{amount}"),
               types.InlineKeyboardButton("❌ Tolak", callback_data=f"rej_{user_id}"))
    
    admin_msg = f"🔔 **Permintaan Deposit Baru**\nUser: {user_id}\nJumlah: {amount}$"
    
    if message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_msg, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(ADMIN_ID, f"{admin_msg}\nBukti: {message.text}", reply_markup=markup, parse_mode="Markdown")
    
    bot.send_message(message.chat.id, "✅ Berhasil dikirim! Mohon tunggu persetujuan admin.")

bot.polling(none_stop=True)