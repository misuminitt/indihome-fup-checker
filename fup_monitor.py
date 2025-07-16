import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import base64

# =============== KONFIGURASI ================
BASE_URL       = "http://192.168.1.1/"
STATS_PAGE     = "state/wireless_state.asp"  # halaman statistik RX/TX
LOGIN_URL      = "goform/webLogin"
USERNAME       = "admin"  # Ganti sesuai router
PASSWORD       = "admin"  # Ganti sesuai router
DELAY_SECONDS  = 300       # Delay cek dalam detik (default: 5 menit)

# Tabel FUP resmi berdasarkan kecepatan paket
FUP_TABLE = {
    20:  (300, 500),
    30:  (400, 600),
    50:  (500, 700),
    100: (800, 1200),
    200: (1200, 1600),
    300: (2000, 3000)
}

# ============== FUNGSI ================
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": urljoin(BASE_URL, "login.html"),
    "X-Requested-With": "XMLHttpRequest"
}

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

    login_data = {
        "username": encoded_username,
        "password": encoded_password
    }

    res = session.post(urljoin(BASE_URL, LOGIN_URL), data=login_data, headers=HEADERS)

    if "menu.html" in res.text or "logout.asp" in res.text or session.cookies.get_dict():
        print("✅ Login berhasil!")
        return True
    else:
        print("❌ Login gagal: tidak ada indikasi login berhasil.")
        return False

def get_usage(session):
    res = session.get(urljoin(BASE_URL, STATS_PAGE), headers=HEADERS, timeout=5)
    soup = BeautifulSoup(res.text, "html.parser")

    try:
        rx_tag = soup.find("td", {"id": "stream_rbc"})
        tx_tag = soup.find("td", {"id": "stream_sbc"})

        if not rx_tag or not tx_tag:
            raise ValueError("❌ Elemen RX/TX tidak ditemukan!")

        rx = int(rx_tag.text.strip())
        tx = int(tx_tag.text.strip())
        total_gb = bytes_to_gb(rx + tx)
        return total_gb, rx, tx

    except Exception:
        print("❌ Debug: Gagal parsing halaman.")
        print(res.text[:1000])
        raise ValueError("❌ Data RX/TX tidak ditemukan di halaman!")

def main():
    # Pilih paket
    print("\n=== IND IHOME FUP MONITOR ===")
    print("Pilih paket speed Anda (Mbps):")
    for speed in sorted(FUP_TABLE):
        print(f" - {speed} Mbps")

    while True:
        try:
            selected = int(input("Masukkan kecepatan paket Anda: "))
            if selected in FUP_TABLE:
                break
            else:
                print("Kecepatan tidak tersedia di daftar.")
        except ValueError:
            print("Input tidak valid. Masukkan angka.")

    stage1, stage2 = FUP_TABLE[selected]

    session = requests.Session()
    if not login_to_router(session):
        print("💡 Coba pastikan tidak ada sesi login terbuka di browser.")
        print("💡 Jika perlu, tunggu 1-2 menit dan coba lagi.")
        print("💡 Jika masih tidak bisa, mungkin salah memilih paket")
        return

    print(f"📱 Mengakses halaman statistik: {STATS_PAGE}")
    print("🔄 Memulai pemantauan penggunaan data WiFi...\n")

    while True:
        try:
            total_gb, rx, tx = get_usage(session)
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] Total: {total_gb:.2f} GB | RX: {bytes_to_gb(rx):.2f} GB | TX: {bytes_to_gb(tx):.2f} GB → {check_fup_status(total_gb, stage1, stage2)}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Gagal ambil data: {e}")
        time.sleep(DELAY_SECONDS)

if __name__ == "__main__":
    main()
