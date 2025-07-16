# 📶 IndiHome FUP Monitor

IndiHome FUP Monitor adalah script Python yang memungkinkan Anda memantau penggunaan data internet (RX/TX) dari router secara otomatis, dengan opsi notifikasi melalui bot Telegram.

Script ini mendukung dua mode:

* 📿 **Mode Terminal (tanpa bot)**
* 🤖 **Mode Telegram Bot (jika diaktifkan)**

---

## 🔧 Fitur

* Cek otomatis pemakaian internet dari halaman statistik router (`wireless_state.asp`)
* Hitung total pemakaian RX + TX dalam GB
* Deteksi status FUP berdasarkan paket langganan Anda (10–300 Mbps)
* Kirim notifikasi ke Telegram secara berkala (jika bot diaktifkan)

---

## 🎞️ Instalasi

1. **Clone repositori**:

   ```bash
   git clone https://github.com/misuminitt/indihome-fup-monitor.git
   cd indihome-fup-monitor
   ```

2. **Install dependensi**:

   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Cara Menjalankan

Jalankan file Python:

```bash
python fup_monitor.py
```

Saat ditanya:

```
Apakah Anda ingin menggunakan bot Telegram? (y/n):
```

Jawab:

* `y` untuk menggunakan mode Telegram bot
* `n` untuk menjalankan hanya di terminal

---

## 🧪 Mode Terminal

Jika Anda memilih `n`, maka:

1. Tabel FUP akan muncul di terminal
2. Anda akan diminta memilih kecepatan paket (contoh: `50`)
3. Pemantauan dimulai dan hasil akan tampil setiap 5 menit

---

## 🤖 Mode Bot Telegram

Jika Anda memilih `y`, Anda perlu menyiapkan bot Telegram terlebih dahulu.

### 🛠️ Cara Membuat Bot Telegram

1. Buka Telegram dan cari bot `@BotFather`

2. Kirim perintah:

   ```
   /start
   /newbot
   ```

3. Masukkan nama bot dan username bot unik (harus diakhiri dengan `bot`, contoh: `indifupbot`)

4. Anda akan menerima **bot token** seperti:

   ```
   123456789:ABCdefGhIjKLMnopQRsTUVwxyz
   ```

5. **Salin token tersebut.**

---

## 📄 Menyimpan Token dan Chat ID

Saat pertama kali menjalankan mode bot:

* Anda akan diminta memasukkan bot token
* Kemudian kirim perintah `/start` ke bot Anda di Telegram
* Bot akan otomatis menyimpan `TELEGRAM_CHAT_ID` di file `.env`

Contoh isi file `.env` setelah setup:

```
TELEGRAM_TOKEN=123456789:ABCdefGhIjKLMnopQRsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

---

## 💬 Perintah Telegram yang Didukung

| Perintah  | Fungsi                                              |
| --------- | --------------------------------------------------- |
| `/start`  | Menampilkan sambutan dan info bot                   |
| `/menu`   | Menampilkan tabel FUP resmi (dalam bentuk gambar)   |
| `/stop`   | Menghentikan pemantauan                             |

---

## 📁 Struktur File

```txt
indihome-fup-monitor/
│
├── fup_monitor.py         # Script utama
├── fup_table.jpg          # Gambar tabel FUP (untuk bot)
├── .env                   # Token dan chat ID (otomatis dibuat)
└── README.md              # Dokumentasi ini
```

---

## 📝 Catatan Tambahan

* Script ini hanya bekerja dengan router yang memiliki halaman `state/wireless_state.asp` dan `goform/webLogin` (seperti ZTE, Fiberhome, dll).
* Pastikan IP gateway router adalah `192.168.1.1` atau sesuaikan variabel `BASE_URL`.

---

## ✅ Lisensi

MIT License © 2025
