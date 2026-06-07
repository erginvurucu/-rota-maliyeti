#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fiyatlar.json otomatik güncelleyici.

Şu an YAKIT fiyatlarını günceller (haftalık değişen tek kalem budur).
Köprü/otoyol/vapur ücretleri yılda bir değiştiği için JSON içinde elle
tutulur; gerektiğinde aşağıdaki yapı genişletilebilir.

Kullanım:
    COLLECTAPI_KEY="apikey xxxxx" python3 guncelle.py

COLLECTAPI_KEY ayarlı değilse script yakıt fiyatlarına dokunmaz,
sadece tarih damgasını günceller (yani güvenle çalışır, bir şeyi bozmaz).

API: https://collectapi.com/api/gasPrice/akaryakit-fiyatlari-api
(Ücretsiz plan mevcut. İstersen Opet/PetrolOfisi sayfasını kazıyan
bir fonksiyonla da değiştirebilirsin.)
"""

import json
import os
import sys
import datetime
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "fiyatlar.json")
CITY = os.environ.get("YAKIT_ILI", "istanbul")


def num(x):
    """'62,95 TL' / '62.95' gibi değerleri float'a çevir."""
    if x is None:
        return None
    s = str(x).replace("TL", "").replace("₺", "").strip()
    s = s.replace(".", "").replace(",", ".") if s.count(",") == 1 and s.count(".") >= 1 else s.replace(",", ".")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def fetch_fuel_collectapi(api_key, city):
    """
    CollectAPI'den il bazlı yakıt fiyatı çeker.
    NOT: CollectAPI yanıt alan adları zamanla değişebilir; ilk çalıştırmada
    ham yanıtı yazdırır, gerekirse aşağıdaki anahtarları ona göre uyarlayın.
    """
    url = f"https://api.collectapi.com/gasPrice/turkeyGasoline?district={city}"
    req = urllib.request.Request(url, headers={
        "content-type": "application/json",
        "authorization": api_key,  # ör. "apikey 1a2b3c..."
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)

    res = data.get("result", data)
    # CollectAPI bazı uçlarda liste, bazılarında sözlük döndürür — ikisini de dene
    if isinstance(res, list) and res:
        res = res[0]

    benzin = num(res.get("gasoline") or res.get("benzine") or res.get("benzin"))
    motorin = num(res.get("diesel") or res.get("motorin"))
    lpg = num(res.get("lpg"))

    if benzin is None and motorin is None:
        print("UYARI: Yakıt alanları tanınamadı. Ham yanıt:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])
    return {"benzin": benzin, "motorin": motorin, "lpg": lpg}


def main():
    with open(JSON_PATH, encoding="utf-8") as f:
        veri = json.load(f)

    bugun = datetime.date.today().isoformat()
    veri["guncelleme_tarihi"] = bugun

    api_key = os.environ.get("COLLECTAPI_KEY")
    if api_key:
        try:
            yeni = fetch_fuel_collectapi(api_key, CITY)
            for k in ("benzin", "motorin", "lpg"):
                if yeni.get(k) is not None:
                    veri["yakit"][k] = yeni[k]
            veri["yakit_ili"] = CITY.capitalize()
            veri["yakit_kaynak"] = "CollectAPI"
            print(f"Yakıt güncellendi: {veri['yakit']}")
        except Exception as e:
            print(f"Yakıt güncellenemedi ({e}); mevcut değerler korundu.")
    else:
        print("COLLECTAPI_KEY yok — yakıt fiyatlarına dokunulmadı, sadece tarih güncellendi.")

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"fiyatlar.json kaydedildi ({bugun}).")


if __name__ == "__main__":
    sys.exit(main())
