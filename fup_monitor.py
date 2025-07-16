import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import base64
import time
import threading
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from dotenv import load_dotenv

# =============== LOAD .env ================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN:
    TELEGRAM_TOKEN = input("Masukkan Telegram Bot Token Anda: ").strip()

if not TELEGRAM_CHAT_ID:
    TELEGRAM_CHAT_ID = None

# Simpan ke .env jika belum ada
if not os.path.exists(".env"):
    with open(".env", "w") as f:
        f.write(f"TELEGRAM_TOKEN={TELEGRAM_TOKEN}\n")
        if TELEGRAM_CHAT_ID:
            f.write(f"TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}\n")

# =============== KONFIGURASI ================
BASE_URL       = "http://192.168.1.1/"
STATS_PAGE     = "state/wireless_state.asp"
LOGIN_URL      = "goform/webLogin"
USERNAME       = "admin"
PASSWORD       = "admin"
DELAY_SECONDS  = 300

FUP_TABLE = {
    20:  (300, 500),
    30:  (400, 600),
    50:  (500, 700),
    100: (800, 1200),
    200: (1200, 1600),
    300: (2000, 3000)
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": urljoin(BASE_URL, "login.html"),
    "X-Requested-With": "XMLHttpRequest"
}

monitor_thread = None
monitoring = False
selected_speed = None
chat_id = None

def bytes_to_gb(b):
    return round(b / (1024 ** 3), 2)

def check_fup_status(total_gb, stage1, stage2):
    if total_gb >= stage2:
        return f"⚠️ FUP-2 tercapai! ({total_gb:.2f} GB) → Speed turun ke 10 Mbps"
    elif total_gb >= stage1:
        return f"🔔 FUP-1 tercapai! ({total_gb:.2f} GB) → Speed turun ke 25 Mbps"
    else:
        return f"✅ Aman — belum melewati FUP. ({total_gb:.2f} GB)"

def login_to_router(session):
    encoded_username = base64.b64encode(USERNAME.encode()).decode()
    encoded_password = base64.b64encode(PASSWORD.encode()).decode()
    login_data = {"username": encoded_username, "password": encoded_password}
    
    try:
        res = session.post(urljoin(BASE_URL, LOGIN_URL), data=login_data, headers=HEADERS, timeout=5)
        if res.status_code == 200 and ("menu.html" in res.text or "logout.asp" in res.text):
            print("✅ Login berhasil!")
            return True
        else:
            print("❌ Login gagal.")
            return False
    except Exception as e:
        print(f"❌ Error saat login: {e}")
        return False

def get_usage(session):
    res = session.get(urljoin(BASE_URL, STATS_PAGE), headers=HEADERS, timeout=5)
    soup = BeautifulSoup(res.text, "html.parser")
    rx_tag = soup.find("td", {"id": "stream_rbc"})
    tx_tag = soup.find("td", {"id": "stream_sbc"})
    if not rx_tag or not tx_tag:
        raise ValueError("❌ Elemen RX/TX tidak ditemukan!")
    rx = int(rx_tag.text.strip())
    tx = int(tx_tag.text.strip())
    return bytes_to_gb(rx + tx), rx, tx

def send_telegram_message(bot, text):
    global chat_id
    if chat_id:
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

def monitor_fup(bot):
    global monitoring, selected_speed
    stage1, stage2 = FUP_TABLE[selected_speed]
    session = requests.Session()
    if not login_to_router(session):
        send_telegram_message(bot, "❌ Gagal login ke router.")
        return

    send_telegram_message(bot, f"📱 Mengakses halaman statistik: {STATS_PAGE}\n🔄 Memulai pemantauan penggunaan data WiFi...")
    print(f"📱 Mengakses halaman statistik: {STATS_PAGE}")
    print("🔄 Memulai pemantauan penggunaan data WiFi...\n")

    while monitoring:
        try:
            total_gb, rx, tx = get_usage(session)
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            status = check_fup_status(total_gb, stage1, stage2)
            message = f"[{ts}] Total: {total_gb:.2f} GB | RX: {bytes_to_gb(rx):.2f} GB | TX: {bytes_to_gb(tx):.2f} GB\n{status}"
            print(message)
            send_telegram_message(bot, message)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Gagal ambil data: {e}")
        time.sleep(DELAY_SECONDS)

def start(update, context):
    global monitoring, chat_id, TELEGRAM_CHAT_ID
    chat_id = update.effective_chat.id
    print(f"📥 Received /start command from {chat_id}")

    # Simpan chat_id ke .env jika belum ada
    if not TELEGRAM_CHAT_ID:
        TELEGRAM_CHAT_ID = str(chat_id)
        with open(".env", "a") as f:
            f.write(f"TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}\n")

    if monitoring:
        update.message.reply_text("⚠️ Pemantauan sudah berjalan!")
        return

    update.message.reply_text("Pilih paket speed Anda (ketik angkanya saja):\n" +
                              "\n".join([f"- {s} Mbps" for s in sorted(FUP_TABLE)]))
    context.user_data['awaiting_speed'] = True

def stop(update, context):
    global monitoring
    monitoring = False
    update.message.reply_text("⛔ Pemantauan dihentikan.")

def handle_message(update, context):
    global monitoring, monitor_thread, selected_speed, chat_id
    chat_id = update.effective_chat.id
    print(f"📨 Pesan masuk dari {chat_id}: {update.message.text}")
    if context.user_data.get('awaiting_speed'):
        try:
            selected = int(update.message.text)
            if selected in FUP_TABLE:
                selected_speed = selected
                update.message.reply_text(f"✅ Paket {selected} Mbps dipilih. Mulai memantau...")
                monitoring = True
                monitor_thread = threading.Thread(target=monitor_fup, args=(context.bot,))
                monitor_thread.start()
                context.user_data['awaiting_speed'] = False
            else:
                update.message.reply_text("❌ Kecepatan tidak tersedia di daftar.")
        except ValueError:
            update.message.reply_text("❌ Input tidak valid. Masukkan angka saja.")

if __name__ == '__main__':
    print("Bot Telegram FUP Monitor sedang berjalan...")
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()
