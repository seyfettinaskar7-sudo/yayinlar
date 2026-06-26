import time
import os
import re
import requests

def temizle():
    # Konsolu temizlemek için (Windows için cls, Mac/Linux için clear)
    os.system('cls' if os.name == 'nt' else 'clear')

def m3u8_bul(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://tvkayseri.com.tr/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        html_content = response.text

        # Güncel m3u8 regex patterni
        m3u8_pattern = r'(https?://[^\s#39;\"\]+\.m3u8[^\s#39;\"\]*)'
        matches = re.findall(m3u8_pattern, html_content)
        unique_links = list(set(matches))

        temizle()
        print("=" * 60)
        print(f"📡 CANLI YAYIN TAKİP ARACI (Son Güncelleme: {time.strftime('%H:%M:%S')})")
        print(f"🔗 Hedef: {url}")
        print("=" * 60)

        if unique_links:
            print(f"\n[✔] {len(unique_links)} Adet Güncel Bağlantı Yakalandı:\n")
            for link in unique_links:
                if "master" in link.lower() or "playlist" in link.lower():
                    print(f"⭐ [MASTER PLAYLIST] -> {link}\n")
                else:
                    print(f"🔗 [YAYIN AKIŞI] -> {link}\n")
        else:
            print("\n[-] Şu an aktif .m3u8 linki bulunamadı. Yayın başlamamış veya player yüklenmemiş olabilir.")
            
        print("=" * 60)
        print("[ℹ] Sistem canlı yayını takip ediyor. Yeniden taranıyor...")

    except Exception as e:
        print(f"[!] Bağlantı hatası: {e}. Yeniden denenecek...")

if __name__ == "__main__":
    hedef_adres = "https://tvkayseri.com.tr/canliyayin"
    
    # KODU SÜREKLİ DÖNGÜDE TUTUYORUZ
    while True:
        m3u8_bul(hedef_adres)
        
        # KAÇ SANİYEDE BİR GÜNCELLESİN? 
        # (Aşağıdaki 300 sayısı 5 dakikaya eşittir (5 * 60). İstersen 60 yapıp her dakika güncelletebilirsin)
        GUNCELLEME_SURESI = 300 
        
        time.sleep(GUNCELLEME_SURESI)
