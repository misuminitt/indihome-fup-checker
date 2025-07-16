import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import base64
import time
import threading
import os
from dotenv import load_dotenv

# Coba import telegram, jika gagal artinya tidak ingin menggunakan bot
try:
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
    telegram_available = True
except ImportError:
    telegram_available = False

# =============== LOAD .env ================
load_dotenv()

TELEGRAM_TOKEN = None
TELEGRAM_CHAT_ID = None

while True:
    use_telegram = input("Apakah Anda ingin menggunakan bot Telegram? (y/n): ").strip().lower()
    if use_telegram in ('y', 'n'):
        break
    print("❌ Masukkan hanya 'y' atau 'n'!")

if use_telegram == 'y':
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if not TELEGRAM_TOKEN:
        TELEGRAM_TOKEN = input("Masukkan Telegram Bot Token Anda: ").strip()

    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(f"TELEGRAM_TOKEN={TELEGRAM_TOKEN}\n")
            if TELEGRAM_CHAT_ID:
                f.write(f"TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}\n")

# =============== KONFIGURASI ================
BASE_URL = "http://192.168.1.1/"
STATS_PAGE = "state/wireless_state.asp"
LOGIN_URL = "goform/webLogin"
USERNAME = "admin"
PASSWORD = "admin"
DELAY_SECONDS = 300

FUP_TABLE = {
    10:  (300, 350),
    20:  (500, 750),
    30:  (700, 1100),
    40:  (800, 1500),
    50:  (1200, 1800),
    100: (1800, 2000),
    200: (3000, 3000),
    300: (4000, 4000),
}

FUP_SPEEDS = {
    10:  (7.5, 3),
    20:  (10, 4),
    30:  (15, 6),
    40:  (20, 8),
    50:  (25, 10),
    100: (50, 20),
    200: (100, None),
    300: (150, None)
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
user_selected_package = {}

def print_fup_table_text():
    print("\n📊 Tabel FUP IndiHome Resmi:")
    print(f"{'Paket (Mbps)':<15}{'FUP-1 (GB)':<12}{'FUP-2 (GB)':<12}")
    print("-" * 40)
    for speed, (fup1, fup2) in FUP_TABLE.items():
        print(f"{speed:<15}{fup1:<12}{fup2:<12}")
    print("\nPilih paket Anda dari daftar di atas.\n")

def bytes_to_gb(b):
    return round(b / (1024 ** 3), 2)

def check_fup_status(total_gb, stage1, stage2, speed):
    speed1, speed2 = FUP_SPEEDS.get(speed, (None, None))
    if total_gb > stage2:
        return f"⚠️ FUP-2 tercapai! ({total_gb:.2f} GB) → Speed turun ke {speed2 or '-'} Mbps"
    elif total_gb > stage1:
        return f"🔔 FUP-1 tercapai! ({total_gb:.2f} GB) → Speed turun ke {speed1 or '-'} Mbps"
    else:
        return f"✅ Aman - belum melewati FUP. ({total_gb:.2f} GB)"

def login_to_router(session):
    encoded_username = base64.b64encode(USERNAME.encode()).decode()
    encoded_password = base64.b64encode(PASSWORD.encode()).decode()
    login_data = {"username": encoded_username, "password": encoded_password}
    res = session.post(urljoin(BASE_URL, LOGIN_URL), data=login_data, headers=HEADERS)
    if "menu.html" in res.text or "logout.asp" in res.text or session.cookies.get_dict():
        print("✅ Login berhasil!")
        return True
    else:
        print("❌ Login gagal: tidak ada indikasi login berhasil.")
        return False

def get_usage(session):
    res = session.get(urljoin(BASE_URL, STATS_PAGE), headers=HEADERS, timeout=5)
    
    # Deteksi kalau halaman berubah menjadi halaman login
    if "login" in res.text.lower() or "goform/webLogin" in res.text:
        raise ConnectionError("Session expired: butuh login ulang.")
    
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
        try:
            bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
        except Exception as e:
            print(f"❌ Gagal kirim pesan ke Telegram: {e}")

def monitor_fup(bot=None):
    global monitoring, selected_speed
    stage1, stage2 = FUP_TABLE[selected_speed]
    session = requests.Session()

    if not login_to_router(session):
        warning_msg = (
            "⚠️ Tidak bisa login ke router.\n"
            "💡 Mungkin sesi login sebelumnya masih aktif atau belum ditutup dengan benar.\n"
            "⏳ Silakan tunggu 1-2 menit lalu coba lagi.\n"
            "🔁 Atau pastikan tidak ada sesi terbuka di browser/router lain."
        )
        if bot:
            send_telegram_message(bot, warning_msg)
        else:
            print(warning_msg)
        monitoring = False
        return

    print(f"📱 Mengakses halaman statistik: {STATS_PAGE}")
    print("🔄 Memantau penggunaan data WiFi...")
    if bot:
        send_telegram_message(bot, f"📱 Mengakses halaman statistik: {STATS_PAGE}\n🔄 Memulai pemantauan penggunaan data WiFi...")

    while monitoring:
        try:
            total_gb, rx, tx = get_usage(session)
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            status = check_fup_status(total_gb, stage1, stage2, selected_speed)
            message = f"[{ts}] Total: {total_gb:.2f} GB | RX: {bytes_to_gb(rx):.2f} GB | TX: {bytes_to_gb(tx):.2f} GB\n{status}"
            print(message)
            if bot:
                send_telegram_message(bot, message)
        except Exception as e:
            error_msg = f"[Error] ❌ Gagal ambil data: {e}"
            print(error_msg)
            if bot and "rx/tx tidak ditemukan" in str(e).lower():
                send_telegram_message(bot, f"❌ Gagal ambil data dari router:\n<b>{e}</b>\n\n💡 Coba cek apakah router masih menyala dan halaman statistik tersedia.")
            elif bot and "session expired" in str(e).lower():
                send_telegram_message(bot, "🔐 Session login router kadaluarsa. Mencoba login ulang...")
                session = requests.Session()
                if not login_to_router(session):
                    send_telegram_message(bot, "❌ Gagal login ulang. Monitoring dihentikan.")
                    monitoring = False
                    return

if __name__ == '__main__':
    print("Bot FUP Monitor sedang berjalan...")
    if use_telegram == 'y' and telegram_available:
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

        def start(update, context):
            global monitoring, chat_id, TELEGRAM_CHAT_ID
            chat_id = update.effective_chat.id
            if not TELEGRAM_CHAT_ID:
                TELEGRAM_CHAT_ID = str(chat_id)
                with open(".env", "a") as f:
                    f.write(f"TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}\n")

            update.message.reply_text(
                "👋 Selamat datang di *IndiHome FUP Monitor*!\n"
                "Bot ini akan memantau total pemakaian data dari router Anda.\n\n"
                "📌 Gunakan /menu untuk memilih paket dan mulai memantau.",
                parse_mode='Markdown'
            )

        def menu(update, context):
            with open("fup_table.jpg", "rb") as f:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=f, caption=(
                    "📊 Berikut adalah Tabel FUP IndiHome Resmi:\n"
                    "Ketik angka paket Anda (misalnya: 50) untuk mulai memantau."
                ))

        def stop(update, context):
            global monitoring
            monitoring = False
            update.message.reply_text("⛔ Pemantauan dihentikan.")

        def handle_message(update, context):
            global monitoring, monitor_thread, selected_speed, chat_id, user_selected_package
            chat_id = update.effective_chat.id
            try:
                selected = int(update.message.text)
                if selected not in FUP_TABLE:
                    update.message.reply_text("❌ Kecepatan tidak tersedia di daftar.")
                    return
                user_selected_package[chat_id] = selected
                selected_speed = selected
                update.message.reply_text(f"✅ Paket {selected} Mbps dipilih. Mulai memantau...")
                monitoring = True
                monitor_thread = threading.Thread(target=monitor_fup, args=(context.bot,))
                monitor_thread.start()
            except ValueError:
                update.message.reply_text("❌ Input tidak valid. Masukkan angka saja.")
            time.sleep(DELAY_SECONDS)

        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("stop", stop))
        dp.add_handler(CommandHandler("menu", menu))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        updater.start_polling()
        updater.idle()
    else:
        print("Telegram tidak digunakan. Menjalankan monitor di terminal...")
        print_fup_table_text()
        try:
            selected_speed = int(input("Masukkan paket speed Anda (misalnya 50): "))
            if selected_speed not in FUP_TABLE:
                raise ValueError("Speed tidak tersedia dalam FUP table.")
            monitoring = True
            monitor_fup()
        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")
