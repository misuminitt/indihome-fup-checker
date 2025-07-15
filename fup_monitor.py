import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import base64

# =============== CONFIG ================
BASE_URL       = "http://192.168.1.1/"
STATS_PAGE     = "state/wireless_state.asp"  # halaman statistik RX/TX
LOGIN_URL      = "goform/webLogin"
USERNAME       = "admin"   # Ganti sesuai router
PASSWORD       = "admin"   # Ganti sesuai router
FUP_STAGE_1    = 1200      # GB
FUP_STAGE_2    = 1800      # GB
DELAY_SECONDS  = 300       # dalam detik (5 menit)
# =======================================

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": urljoin(BASE_URL, "login.html"),
    "X-Requested-With": "XMLHttpRequest"  # ⬅️ Tambahan ini
}

def bytes_to_gb(b):
    return round(b / (1024**3), 2)

def check_fup_status(total_gb):
    if total_gb >= FUP_STAGE_2:
        return f"⚠️ FUP-2 tercapai! ({total_gb:.2f} GB) → Speed turun ke 10 Mbps"
    elif total_gb >= FUP_STAGE_1:
        return f"🔔 FUP-1 tercapai! ({total_gb:.2f} GB) → Speed turun ke 25 Mbps"
    else:
        return f"✅ Aman — belum melewati FUP. ({total_gb:.2f} GB)"

def login_to_router(session):
    # Encode username dan password ke Base64 karena JS melakukan itu
    encoded_username = base64.b64encode(USERNAME.encode()).decode()
    encoded_password = base64.b64encode(PASSWORD.encode()).decode()

    login_data = {
        "username": encoded_username,
        "password": encoded_password
    }

    login_url = urljoin(BASE_URL, "goform/webLogin")
    res = session.post(login_url, data=login_data, headers=HEADERS)

    print("📦 Cookies setelah login:", session.cookies.get_dict())
    print("📩 Headers respon login:", res.headers)

    # Debug sukses login berdasarkan redirect atau cookie
    if "menu.html" in res.text or "logout.asp" in res.text or session.cookies.get_dict():
        print("✅ Login berhasil!")
    else:
        print("❌ Login gagal: tidak ada indikasi login berhasil.")

def get_usage(session):
    res = session.get(urljoin(BASE_URL, STATS_PAGE), headers=HEADERS, timeout=5)

    # Deteksi sesi kadaluarsa
    if "Return2login" in res.text or "login.html" in res.text:
        raise ConnectionError("⚠️ Sesi kadaluarsa — butuh login ulang.")

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
    session = requests.Session()

    login_to_router(session)
    print(f"📡 Mengakses halaman statistik: {STATS_PAGE}")
    print("🔄 Memulai pemantauan penggunaan data WiFi...\n")

    while True:
        try:
            total_gb, rx, tx = get_usage(session)
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] Total: {total_gb:.2f} GB | RX: {bytes_to_gb(rx):.2f} GB | TX: {bytes_to_gb(tx):.2f} GB → {check_fup_status(total_gb)}")
        
        except ConnectionError as ce:
            print(f"[{time.strftime('%H:%M:%S')}] 🔁 {ce} → Melakukan login ulang...")
            login_to_router(session)  # login ulang
            continue  # ulangi tanpa delay

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Gagal ambil data: {e}")
        
        time.sleep(DELAY_SECONDS)

if __name__ == "__main__":
    main()
