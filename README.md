# indihome-fup-checker

Script Python sederhana untuk memantau pemakaian data internet (RX/TX) dari router Indihome dan memberikan peringatan saat melewati batas FUP (Fair Usage Policy).

## 🔧 Fitur

- Otomatis login ke router
- Mengambil statistik RX (download) dan TX (upload)
- Menampilkan total pemakaian dalam satuan GB
- Memberikan peringatan saat mencapai FUP-1 (misal 1200 GB) atau FUP-2 (misal 1800 GB)
- Cek otomatis setiap beberapa menit

## 📷 Contoh Output

```
[2025-07-16 05:51:58] Total: 2.42 GB | RX: 1.85 GB | TX: 0.57 GB → ✅ Aman — belum melewati FUP. (2.42 GB)
```

## ⚙️ Konfigurasi

Edit bagian ini di dalam `fup_monitor.py`:

```python
BASE_URL       = "http://192.168.1.1/"   # IP router kamu
USERNAME       = "admin"                 # Username login router
PASSWORD       = "admin"                 # Password login router
FUP_STAGE_1    = 1200                    # FUP tahap 1 dalam GB
FUP_STAGE_2    = 1800                    # FUP tahap 2 dalam GB
DELAY_SECONDS  = 300                     # Interval pengecekan dalam detik
```

> ⚠️ Pastikan endpoint statistik `state/wireless_state.asp` sesuai dengan router kamu. Beberapa router mungkin menggunakan halaman lain.

## 🚀 Cara Menjalankan

1. Install dependency:
    ```
    pip install requests beautifulsoup4
    ```

2. Jalankan script:
    ```
    python fup_monitor.py
    ```

## 📝 Catatan Tambahan

- Script ini bekerja pada router tertentu yang menyajikan data statistik RX/TX lewat HTML.
- Beberapa router menggunakan proteksi JavaScript tambahan atau session berbeda, silakan sesuaikan jika perlu.
- Login dilakukan menggunakan username dan password yang di-*Base64* terlebih dahulu, sesuai dengan proses di halaman login router.

## 📄 Lisensi

MIT License — bebas digunakan dan dimodifikasi.
