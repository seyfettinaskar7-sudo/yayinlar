import re
import requests

def m3u8_bul(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        print(f"[+] {url} adresi taranıyor...")
        response = requests.get(url, headers=headers, timeout=10)
        html_content = response.text

        m3u8_pattern = r'(https?://[^\s#39;\"]+\.m3u8[^\s#39;\"]*)'
        matches = re.findall(m3u8_pattern, html_content)
        unique_links = list(set(matches))

        if unique_links:
            print(f"\n[✔] {len(unique_links)} adet .m3u8 bulundu:\n")
            for link in unique_links:
                print(f"-> {link}")
        else:
            print("\n[-] Bağlantı bulunamadı.")
    except Exception as e:
        print(f"[!] Hata: {e}")

if __name__ == "__main__":
    # BURAYA YAZACAKSIN: Taramak istediğin adresi aşağıdaki tırnakların içine yapıştır
    hedef_adres = "https://buraya-taratmak-istedigin-siteyi-yaz.com"
    
    m3u8_bul(hedef_adres)
