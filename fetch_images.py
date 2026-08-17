"""Скачивание реальных фото для портфолио-сайта Furnio.

Берёт конкретные файлы Wikimedia Commons по точным названиям (свободная лицензия)
и сохраняет их:
  - static/img/products/<slug>.jpg   — фото товаров
  - static/img/categories/<slug>.jpg — фото категорий
  - static/img/lookbook/<name>.jpg   — фото интерьеров (блок «Интерьеры»)
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "static", "img")

UA = {"User-Agent": "FurnioPortfolio/1.0 (portfolio project; contact: hello@furnio.ru)"}

MAP = [
    # (имя товара, точное название файла на Commons)
    ("Диван «Модерн» трёхместный",
     "File:Couch-furniture-living-room-sofa (24300293356).jpg"),
    ("Диван «Грэйс» угловой",
     "File:Cozy living room with a gray sofa.jpg"),
    ("Диван-кровать «Лофт»",
     "File:EFTA00000372 - Modern living room features a white sofa a plush ottoman with fur and mirrored walls reflecting the spaces sleek design.jpg"),
    ("Диван «Комфорт» двухместный",
     "File:EFTA00000536 - Modern minimalist living room with white furniture reflective surfaces and a sleek design featuring a large sofa and a glass coffee table.jpg"),

    ("Кресло «Скандинавия»",
     "File:EFTA00000034 - Modern living room with a white armchair bookshelf filled with books and a patterned rug on dark flooring.jpg"),
    ("Кресло-качалка «Вуд»",
     "File:Cozy living room with tropical patterned armchair and natural light from large windows.jpg"),
    ("Кресло «Бергамо» с подлокотниками",
     "File:A plush green velvet armchair occupies the corner of a bright living room.jpg"),
    ("Кресло-реклайнер «Рокко»",
     "File:EFTA00000287 - Well-lit living room with beige carpet cream armchairs green upholstered furniture and large windows dressed in light drapes.jpg"),

    ("Обеденный стол «Оак»",
     "File:22 West - dining table.jpg"),
    ("Журнальный столик «Модерн»",
     "File:Coffee Table.jpg"),
    ("Письменный стол «Студио»",
     "File:Рабочий стол в интерьере.jpg"),
    ("Кухонный стол «Флоренция»",
     "File:EFTA00002125 - Kitchen dining area with a white table black chairs and a stainless steel refrigerator featuring two windows with frosted glass.jpg"),

    ("Кровать «Винтаж» с изголовьем",
     "File:Balanced Modern Bedroom Design with Neutral Tones and Layered Lighting.jpg"),
    ("Кровать «Монтевидео» двуспальная",
     "File:Cozy modern bedroom with plush pillows and elegant drapes in bright daylight.jpg"),
    ("Кровать-подиум «Токио»",
     "File:Modern bedroom design featuring colorful headboard and plush pillows in a contemporary setting.jpg"),
    ("Кровать «Норд» односпальная",
     "File:Stylish bedroom interior featuring a unique headboard design with geometric patterns and elegant bedding decor.jpg"),

    ("Шкаф-купе «Альпина»",
     "File:176 Nile Street master bedroom wardrobe ensuite.jpg"),
    ("Шкаф «Лион» четырёхдверный",
     "File:EFTA00001674 - Bright minimalist bedroom with a white desk and chair a colorful zigzag rug and a wooden wardrobe under a vaulted ceiling.jpg"),
    ("Комод «Бельгия»",
     "File:EFTA00000298 - Bedroom with purple walls a wooden dresser a television and a striped fur blanket on the bed.jpg"),
    ("Стеллаж «Графит»",
     "File:Billy Bookcase (cropped).jpg"),

    ("Полка навесная «Леон»",
     "File:20140708 Radkersburg - Etagere H3558.jpg"),
    ("Комод «Окленд»",
     "File:20240608 kredens sideboard Katowice Panewniki.jpg"),
    ("Тумба прикроватная «Флор»",
     "File:Bed & Nightstand (49875912823).jpg"),
    ("Этажерка «Трио»",
     "File:USVI IMG 5227 - Cozy eclectic living room with exposed beams stone walls and vintage furniture featuring a large bookshelf art displays and warm lighting.jpg"),
]


CATS = [
    # (slug категории, точное название файла на Commons)
    ("divany",
     "File:Modern living room with stylish furniture and a view of the outdoors in a cozy apartment setting.jpg"),
    ("kresla",
     "File:EFTA00002057 - Cozy living room with stone walls a fireplace and modern furniture featuring a wooden coffee table and plush armchairs.jpg"),
    ("stoly",
     "File:A modern dinner set, table and chairs in a beach house, Auckland - 1028.jpg"),
    ("krovati",
     "File:Modern bedroom design in a stylish hotel room featuring geometric patterns and soft linens.jpg"),
    ("shkafy",
     "File:Elfa storage system behind mirrored doors in bedroom.jpg"),
    ("polki",
     "File:Interior of Willistead Manor (bookshelf), Windsor, Ontario, 2025-06-07.jpg"),
]

LOOKBOOK = [
    # (имя карточки, точное название файла на Commons)
    ("living-room",
     "File:Gene Zema house showing living room, Seattle (4669580613).jpg"),
    ("bedroom",
     "File:Hôtel Château Cran Chaud Chicoutimi - Suite avec lit King.jpg"),
    ("dining",
     "File:Modern kitchen and dining area in a bright apartment on a sunny day with simple decor and furniture.jpg"),
]

HERO = [
    ("hero.jpg",
     "File:Cozy living room setting with a yellow sofa and a coffee table adorned with cups and a flower pot.jpg"),
]


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[«»\"']", "", text)
    text = re.sub(r"[^a-zа-яё0-9]+", "-", text)
    return text.strip("-")


def get_info(title, retries=3):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "titles": title,
        "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": 1200,
    })
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                return p.get("imageinfo", [{}])[0]
            return None
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2)


def main():
    groups = [
        (os.path.join(IMG, "products"), "products", MAP,
         lambda name: slugify(name) + ".jpg"),
        (os.path.join(IMG, "categories"), "categories", CATS,
         lambda slug: slug + ".jpg"),
        (os.path.join(IMG, "lookbook"), "lookbook", LOOKBOOK,
         lambda name: name + ".jpg"),
        (IMG, "hero", HERO, lambda name: name),
    ]
    ok, fail = 0, 0
    for out_dir, label, entries, name_fn in groups:
        os.makedirs(out_dir, exist_ok=True)
        for name, title in entries:
            fname = name_fn(name)
            path = os.path.join(out_dir, fname)
            try:
                info = get_info(title)
                if not info or info.get("mime") != "image/jpeg":
                    print(f"SKIP {label}/{fname}: bad info")
                    fail += 1
                    continue
                url = info.get("thumburl") or info.get("url")
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
                    f.write(r.read())
                print(f"OK {label}/{fname}  ({info.get('width')}px)  <- {title}")
                ok += 1
            except Exception as e:
                print(f"FAIL {label}/{fname}: {type(e).__name__}: {e}")
                fail += 1
            time.sleep(0.6)
    print(f"\nDone: {ok} ok, {fail} fail -> {IMG}")


if __name__ == "__main__":
    main()