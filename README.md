# IndiHome FUP Monitor via Router Fiberhome

Cek pemakaian bandwidth WiFi dan status FUP (Fair Usage Policy) secara realtime langsung dari router tanpa perangkat tambahan.

## Fitur
- Scrape data dari halaman `Wireless Status`
- Hitung total penggunaan (GB)
- Peringatan jika sudah mencapai FUP-1 / FUP-2 (sesuai paket)
- Real-time log setiap 5 menit

## Cara Pakai

1. Install dependensi:

pip install -r requirements.txt

2. Jalankan:

python fup_monitor.py

3. Ubah konfigurasi paket dan URL router di bagian atas script (`BASE_URL`, `FUP_STAGE_1`, `FUP_STAGE_2`).

## Catatan
- Hanya menghitung trafik via **WiFi**, bukan LAN.
- Tidak perlu router tambahan atau Mikrotik.
