import os
import re
import sqlite3
from datetime import datetime, timedelta

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    image TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    material TEXT NOT NULL DEFAULT '',
    dimensions TEXT NOT NULL DEFAULT '',
    warranty TEXT NOT NULL DEFAULT '',
    price INTEGER NOT NULL,
    old_price INTEGER,
    stock INTEGER NOT NULL DEFAULT 0,
    is_featured INTEGER NOT NULL DEFAULT 0,
    image TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL,
    comment TEXT NOT NULL DEFAULT '',
    payment TEXT NOT NULL DEFAULT 'cash',
    total INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    qty INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_featured ON products(is_featured);
"""

CATEGORIES = [
    {
        "name": "Диваны",
        "slug": "divany",
        "description": "Комфортные диваны на каждый день и для гостиной",
        "image": "category-divany.svg",
        "color": "#b5713c",
        "color2": "#d99a62",
    },
    {
        "name": "Кресла",
        "slug": "kresla",
        "description": "Уютные кресла и реклайнеры для отдыха",
        "image": "category-kresla.svg",
        "color": "#3f7d7c",
        "color2": "#5fa8a6",
    },
    {
        "name": "Столы",
        "slug": "stoly",
        "description": "Обеденные, журнальные и рабочие столы",
        "image": "category-stoly.svg",
        "color": "#8a6a45",
        "color2": "#b0885d",
    },
    {
        "name": "Кровати",
        "slug": "krovati",
        "description": "Кровати и основания с ортопедическими ламелями",
        "image": "category-krovati.svg",
        "color": "#5b5f97",
        "color2": "#7c81bd",
    },
    {
        "name": "Шкафы",
        "slug": "shkafy",
        "description": "Шкафы-купе, гардеробные и комоды",
        "image": "category-shkafy.svg",
        "color": "#4f6d5a",
        "color2": "#6f917c",
    },
    {
        "name": "Полки и комоды",
        "slug": "polki",
        "description": "Стеллажи, полки и тумбы для порядка в доме",
        "image": "category-polki.svg",
        "color": "#8b5f7a",
        "color2": "#aa7c98",
    },
]

PRODUCTS = [
    # Диваны
    {"category": "divany", "name": "Диван «Модерн» трёхместный", "price": 89900, "old_price": 109900, "stock": 6, "featured": 1,
     "material": "Рогожка, сосновый каркас", "dimensions": "220 × 95 × 85 см", "warranty": "18 месяцев",
     "description": "Трёхместный диван с глубокими посадочными местами и съёмными чехлами. Каркас из массива сосны, наполнение — ППУ повышенной плотности. Легко разбирается для транспортировки."},
    {"category": "divany", "name": "Диван «Грэйс» угловой", "price": 129900, "stock": 3, "featured": 1,
     "material": "Велюр, фанера, металлокаркас", "dimensions": "280 × 170 × 88 см", "warranty": "24 месяца",
     "description": "Просторный угловой диван с нишей для белья и раскладным механизмом «дельфин». Плотный велюр, устойчивый к истиранию. Идеален для просторных гостиных."},
    {"category": "divany", "name": "Диван-кровать «Лофт»", "price": 74900, "stock": 8, "featured": 0,
     "material": "Экокожа, ДСП", "dimensions": "200 × 90 × 80 см", "warranty": "12 месяцев",
     "description": "Компактный диван-кровать с механизмом «еврокнижка». Экокожа легко чистится, подходит для малогабаритных квартир и студий."},
    {"category": "divany", "name": "Диван «Комфорт» двухместный", "price": 59900, "old_price": 67900, "stock": 12, "featured": 0,
     "material": "Флок, берёзовый каркас", "dimensions": "160 × 92 × 84 см", "warranty": "18 месяцев",
     "description": "Классический двухместный диван с высокой спинкой. Бюджетное решение для кухни или прихожей. Подлокотники с деревянными вставками."},

    # Кресла
    {"category": "kresla", "name": "Кресло «Скандинавия»", "price": 34900, "stock": 9, "featured": 1,
     "material": "Хлопковый твид, бук", "dimensions": "78 × 82 × 92 см", "warranty": "18 месяцев",
     "description": "Скандинавское кресло на каркасе из бука с мягкой подушкой сиденья. Светлый твид придаёт интерьеру уют и воздушность."},
    {"category": "kresla", "name": "Кресло-качалка «Вуд»", "price": 29900, "stock": 5, "featured": 0,
     "material": "Массив ясеня, хлопок", "dimensions": "70 × 100 × 95 см", "warranty": "24 месяца",
     "description": "Классическая качалка из цельного ясеня с мягкой подушкой. Снимает напряжение после рабочего дня и отлично вписывается в любой интерьер."},
    {"category": "kresla", "name": "Кресло «Бергамо» с подлокотниками", "price": 41900, "stock": 4, "featured": 1,
     "material": "Велюр, металлокаркас", "dimensions": "82 × 80 × 90 см", "warranty": "18 месяцев",
     "description": "Кресло с широкими подлокотниками и глубокой посадкой. Металлокаркас выдерживает до 150 кг. Мягкий велюр нескольких оттенков на выбор."},
    {"category": "kresla", "name": "Кресло-реклайнер «Рокко»", "price": 54900, "stock": 2, "featured": 0,
     "material": "Искусственная кожа, сталь", "dimensions": "90 × 110 × 105 см", "warranty": "24 месяца",
     "description": "Механический реклайнер с откидной спинкой и подставкой для ног. Стальной механизм рассчитан на 30 000 циклов раскладывания."},

    # Столы
    {"category": "stoly", "name": "Обеденный стол «Оак»", "price": 47900, "stock": 7, "featured": 1,
     "material": "Массив дуба", "dimensions": "180 × 90 × 75 см", "warranty": "36 месяцев",
     "description": "Обеденный стол из массива дуба с натуральным маслом. Вмещает до 8 человек. Столешница толщиной 40 мм — устойчива к царапинам и влаге."},
    {"category": "stoly", "name": "Журнальный столик «Модерн»", "price": 19900, "stock": 15, "featured": 0,
     "material": "МДФ, металл", "dimensions": "90 × 45 × 40 см", "warranty": "18 месяцев",
     "description": "Лаконичный журнальный столик с полкой для хранения. Металлические ножки в порошковой окраске. Подходит к большинству стилей интерьера."},
    {"category": "stoly", "name": "Письменный стол «Студио»", "price": 32900, "old_price": 37900, "stock": 10, "featured": 1,
     "material": "ЛДСП Egger, металл", "dimensions": "140 × 60 × 76 см", "warranty": "24 месяца",
     "description": "Рабочий стол с кабель-каналом и выдвижным ящиком. Столешница из немецкого ЛДСП с защитной кромкой. Идеален для домашнего офиса."},
    {"category": "stoly", "name": "Кухонный стол «Флоренция»", "price": 27900, "stock": 11, "featured": 0,
     "material": "Шпон ореха, металл", "dimensions": "120 × 80 × 74 см", "warranty": "18 месяцев",
     "description": "Компактный кухонный стол со скруглёнными углами. Шпон ореха на МДФ, ножки из матовой стали. Разбирается на две части для хранения."},

    # Кровати
    {"category": "krovati", "name": "Кровать «Винтаж» с изголовьем", "price": 96900, "stock": 3, "featured": 1,
     "material": "Массив берёзы, текстиль", "dimensions": "200 × 180 × 120 см", "warranty": "36 месяцев",
     "description": "Кровать с мягким каретным изголовьем и ортопедическими ламелями. Массив берёзы с тонировкой «венеция». Для матрасов 180×200."},
    {"category": "krovati", "name": "Кровать «Монтевидео» двуспальная", "price": 84900, "old_price": 94900, "stock": 5, "featured": 0,
     "material": "ЛДСП, экошпон", "dimensions": "200 × 160 × 95 см", "warranty": "24 месяца",
     "description": "Строгая двуспальная кровать с нишей для белья. Каркас усиленными рёбрами жёсткости. Подходит для матрасов 160×200."},
    {"category": "krovati", "name": "Кровать-подиум «Токио»", "price": 69900, "stock": 6, "featured": 1,
     "material": "МДФ, LED-подсветка", "dimensions": "210 × 190 × 40 см", "warranty": "18 месяцев",
     "description": "Кровать-подиум с подсветкой и мягким изголовьем. Низкий силуэт визуально увеличивает пространство спальни. Матрас 180×200."},
    {"category": "krovati", "name": "Кровать «Норд» односпальная", "price": 49900, "stock": 8, "featured": 0,
     "material": "Массив сосны", "dimensions": "200 × 90 × 75 см", "warranty": "36 месяцев",
     "description": "Односпальная кровать из массива сосны с эффектом «белёный дуб». Ортопедическое основание с ламелями в комплекте."},

    # Шкафы
    {"category": "shkafy", "name": "Шкаф-купе «Альпина»", "price": 119900, "old_price": 139900, "stock": 2, "featured": 1,
     "material": "ЛДСП Egger, зеркало", "dimensions": "250 × 60 × 240 см", "warranty": "24 месяца",
     "description": "Трёхдверный шкаф-купе с зеркальной центральной дверью. Внутри — антресоли, штанга и полки. Направляющие с доводчиками."},
    {"category": "shkafy", "name": "Шкаф «Лион» четырёхдверный", "price": 92900, "stock": 4, "featured": 0,
     "material": "МДФ, фанера", "dimensions": "200 × 58 × 220 см", "warranty": "18 месяцев",
     "description": "Классический четырёхдверный шкаф с филенчатыми фасадами. Внутреннее наполнение: полки, ящики и штанги под два ряда вещей."},
    {"category": "shkafy", "name": "Комод «Бельгия»", "price": 38900, "stock": 9, "featured": 1,
     "material": "Шпон ясеня", "dimensions": "120 × 45 × 85 см", "warranty": "24 месяца",
     "description": "Комод на пять ящиков с направляющими полного выдвижения. Шпон ясеня с натуральной текстурой. Нагрузка на ящик до 15 кг."},
    {"category": "shkafy", "name": "Стеллаж «Графит»", "price": 24900, "stock": 14, "featured": 0,
     "material": "ЛДСП, металл", "dimensions": "100 × 40 × 190 см", "warranty": "18 месяцев",
     "description": "Высокий открытый стеллаж на пять полок. Комбинированная конструкция из ЛДСП и металлокаркаса. Нагрузка на полку до 25 кг."},

    # Полки и комоды
    {"category": "polki", "name": "Полка навесная «Леон»", "price": 8900, "stock": 20, "featured": 0,
     "material": "Массив сосны", "dimensions": "80 × 22 × 12 см", "warranty": "12 месяцев",
     "description": "Навесная полка из массива сосны со скрытым креплением. Выдерживает до 8 кг. Крепёж в комплекте."},
    {"category": "polki", "name": "Комод «Окленд»", "price": 31900, "stock": 7, "featured": 1,
     "material": "ЛДСП, шпон ореха", "dimensions": "110 × 42 × 90 см", "warranty": "18 месяцев",
     "description": "Комод на четыре ящика с плавным закрытием. Комбинированная отделка шпоном ореха и матовым ЛДСП. Подойдёт в спальню и гостиную."},
    {"category": "polki", "name": "Тумба прикроватная «Флор»", "price": 12900, "stock": 18, "featured": 0,
     "material": "МДФ, ротанг", "dimensions": "45 × 38 × 55 см", "warranty": "12 месяцев",
     "description": "Прикроватная тумба с фасадом из ротанга и двумя выдвижными ящиками. Светлый МДФ подходит к скандинавскому стилю."},
    {"category": "polki", "name": "Этажерка «Трио»", "price": 16900, "stock": 10, "featured": 1,
     "material": "Металл, массив", "dimensions": "60 × 30 × 115 см", "warranty": "24 месяца",
     "description": "Трёхъярусная этажерка с металлическими стойками и деревянными полками. Устойчивая конструкция с противоскользящими ножками."},
]

SORT_OPTIONS = {
    "popular": "ORDER BY p.is_featured DESC, p.created_at DESC",
    "price_asc": "ORDER BY p.price ASC",
    "price_desc": "ORDER BY p.price DESC",
    "new": "ORDER BY p.created_at DESC",
    "name": "ORDER BY p.name ASC",
}


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[«»\"']", "", text)
    text = re.sub(r"[^a-zа-яё0-9]+", "-", text)
    return text.strip("-")


def connect_db(app):
    db_path = os.path.join(app.instance_path, "furniture.db")
    os.makedirs(app.instance_path, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db


def query(db, sql, args=()):
    return db.execute(sql, args).fetchall()


def get_categories(db):
    return query(db, "SELECT * FROM categories ORDER BY id")


def get_category_by_slug(db, slug):
    rows = query(db, "SELECT * FROM categories WHERE slug = ?", (slug,))
    return dict(rows[0]) if rows else None


def get_product(db, product_id):
    rows = query(db, "SELECT p.*, c.name AS category_name, c.slug AS category_slug "
                     "FROM products p JOIN categories c ON c.id = p.category_id "
                     "WHERE p.id = ?", (product_id,))
    return dict(rows[0]) if rows else None


def get_product_by_slug(db, slug):
    rows = query(db, "SELECT p.*, c.name AS category_name, c.slug AS category_slug "
                     "FROM products p JOIN categories c ON c.id = p.category_id "
                     "WHERE p.slug = ?", (slug,))
    return dict(rows[0]) if rows else None


def get_products(db, category_id=None, featured=False, limit=None, exclude_id=None, order_by=None):
    sql = ("SELECT p.*, c.name AS category_name, c.slug AS category_slug "
           "FROM products p JOIN categories c ON c.id = p.category_id WHERE 1=1")
    params = []
    if category_id:
        sql += " AND p.category_id = ?"
        params.append(category_id)
    if featured:
        sql += " AND p.is_featured = 1"
    if exclude_id:
        sql += " AND p.id != ?"
        params.append(exclude_id)
    sql += " " + SORT_OPTIONS.get(order_by or "popular", SORT_OPTIONS["popular"])
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    return query(db, sql, params)


def search_products(db, category=None, search=None, sort="popular",
                    price_min=None, price_max=None, in_stock_only=False):
    sql = ("SELECT p.*, c.name AS category_name, c.slug AS category_slug "
           "FROM products p JOIN categories c ON c.id = p.category_id WHERE 1=1")
    params = []
    if category:
        sql += " AND c.slug = ?"
        params.append(category)
    if search:
        sql += " AND (LOWER(p.name) LIKE ? OR LOWER(p.description) LIKE ? OR LOWER(p.material) LIKE ?)"
        like = f"%{search.lower()}%"
        params.extend([like, like, like])
    if price_min is not None:
        sql += " AND p.price >= ?"
        params.append(price_min)
    if price_max is not None:
        sql += " AND p.price <= ?"
        params.append(price_max)
    if in_stock_only:
        sql += " AND p.stock > 0"
    sql += " " + SORT_OPTIONS.get(sort, SORT_OPTIONS["popular"])
    return query(db, sql, params)


def create_order(db, name, phone, email, address, comment, payment, total, items):
    now = datetime.now().isoformat(timespec="seconds")
    cur = db.execute(
        "INSERT INTO orders (name, phone, email, address, comment, payment, total, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?)",
        (name, phone, email, address, comment, payment, total, now),
    )
    order_id = cur.lastrowid
    for item in items:
        db.execute(
            "INSERT INTO order_items (order_id, product_id, name, price, qty) VALUES (?, ?, ?, ?, ?)",
            (order_id, item["product_id"], item["name"], item["price"], item["qty"]),
        )
        db.execute("UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?",
                   (item["qty"], item["product_id"]))
    db.commit()
    return order_id


def get_order(db, order_id):
    rows = query(db, "SELECT * FROM orders WHERE id = ?", (order_id,))
    if not rows:
        return None
    order = dict(rows[0])
    order["created_at"] = datetime.fromisoformat(order["created_at"])
    order["items"] = query(db, "SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    return order


# ---------- SVG images ----------


def _pill(cx, cy, w, h, rx, fill, opacity=1.0):
    return f'<rect x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" opacity="{opacity}"/>'


def _rect(x, y, w, h, rx, fill, opacity=1.0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" opacity="{opacity}"/>'


def _ellipse(cx, cy, rx, ry, fill):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"/>'


def _legs(y, x1, x2, h=26, color="#3a322c"):
    return (
        _rect(x1, y, 16, h, 4, color)
        + _rect(x2, y, 16, h, 4, color)
    )


def draw_sofa(accent):
    body = "#4a413a"
    parts = []
    parts.append(_rect(150, 330, 500, 118, 26, body))            # seat base
    parts.append(_rect(150, 170, 500, 180, 26, body))            # backrest
    parts.append(_rect(95, 235, 62, 215, 22, body))              # left arm
    parts.append(_rect(643, 235, 62, 215, 22, body))             # right arm
    parts.append(_rect(190, 300, 210, 88, 16, accent, 0.92))     # left cushion
    parts.append(_rect(420, 300, 190, 88, 16, accent, 0.92))     # right cushion
    parts.append(_pill(262, 130, 130, 62, 22, "#e9b9a0"))        # pillow 1
    parts.append(_pill(510, 128, 120, 56, 20, "#d9e4e0"))        # pillow 2
    parts.append(_legs(448, 185, 605, 30))
    return "".join(parts)


def draw_armchair(accent):
    body = "#4a413a"
    parts = []
    parts.append(_rect(225, 400, 350, 105, 24, body))            # seat
    parts.append(_rect(225, 245, 350, 175, 24, body))            # back
    parts.append(_rect(170, 315, 62, 190, 22, body))             # left arm
    parts.append(_rect(568, 315, 62, 190, 22, body))             # right arm
    parts.append(_rect(255, 370, 290, 76, 16, accent, 0.92))     # cushion
    parts.append(_pill(340, 210, 120, 56, 20, "#e9b9a0"))        # pillow
    parts.append(_legs(505, 245, 525, 26))
    return "".join(parts)


def draw_table(accent):
    parts = []
    parts.append(_rect(120, 240, 560, 44, 18, "#8a6a45"))        # top
    parts.append(_rect(175, 284, 20, 190, 6, "#4a413a"))         # leg left
    parts.append(_rect(605, 284, 20, 190, 6, "#4a413a"))         # leg right
    parts.append(_rect(140, 474, 90, 16, 8, "#4a413a"))          # left foot
    parts.append(_rect(570, 474, 90, 16, 8, "#4a413a"))          # right foot
    parts.append(_pill(410, 222, 90, 34, 16, accent, 0.9))       # center accent bar
    parts.append(_ellipse(300, 235, 26, 14, "#5f7d5c"))          # vase
    parts.append(_rect(296, 210, 8, 26, 4, "#7a6a55"))           # vase neck
    return "".join(parts)


def draw_bed(accent):
    parts = []
    parts.append(_rect(130, 300, 540, 60, 12, "#4a413a"))        # headboard
    parts.append(_rect(130, 230, 540, 90, 18, accent, 0.85))     # padded headboard
    parts.append(_rect(120, 350, 560, 150, 18, "#4a413a"))       # frame
    parts.append(_rect(145, 362, 510, 118, 12, "#f3ede4"))       # mattress
    parts.append(_pill(215, 350, 130, 60, 20, "#e9b9a0"))        # pillow
    parts.append(_pill(360, 348, 120, 52, 18, "#cfe0da"))        # pillow
    parts.append(_pill(500, 360, 150, 40, 16, accent, 0.75))     # blanket
    parts.append(_legs(500, 160, 630, 24))
    return "".join(parts)


def draw_wardrobe(accent):
    parts = []
    parts.append(_rect(175, 150, 450, 380, 14, "#4a413a"))       # body
    parts.append(_rect(195, 168, 205, 344, 8, accent, 0.85))     # left door
    parts.append(_rect(400, 168, 205, 344, 8, accent, 0.85))     # right door
    parts.append(_rect(262, 330, 10, 48, 4, "#4a413a"))          # left handle
    parts.append(_rect(528, 330, 10, 48, 4, "#4a413a"))          # right handle
    parts.append(_legs(530, 215, 575, 20))
    return "".join(parts)


def draw_shelf(accent):
    parts = []
    parts.append(_rect(165, 150, 24, 340, 8, "#4a413a"))         # left side
    parts.append(_rect(611, 150, 24, 340, 8, "#4a413a"))         # right side
    parts.append(_rect(160, 180, 480, 22, 8, "#4a413a"))         # top shelf
    parts.append(_rect(160, 320, 480, 22, 8, "#4a413a"))         # middle shelf
    parts.append(_rect(160, 460, 480, 22, 8, "#4a413a"))         # bottom shelf
    # items on shelves
    parts.append(_rect(210, 232, 40, 88, 6, accent, 0.9))        # book stack
    parts.append(_rect(268, 252, 34, 68, 6, "#c9b7a5"))          # book
    parts.append(_rect(320, 240, 48, 80, 8, "#5f7d5c"))          # box
    parts.append(_ellipse(560, 232, 26, 20, "#e9b9a0"))          # vase
    parts.append(_rect(540, 202, 40, 30, 8, "#c9b7a5"))          # vase body
    parts.append(_rect(400, 240, 70, 80, 8, "#cfe0da"))          # box 2
    parts.append(_rect(220, 372, 60, 88, 8, "#cfe0da"))          # box bottom
    parts.append(_rect(300, 392, 40, 68, 6, accent, 0.85))       # book bottom
    parts.append(_ellipse(560, 382, 24, 18, "#5f7d5c"))          # plant bottom
    return "".join(parts)


DRAW_FUNCS = {
    "divany": draw_sofa,
    "kresla": draw_armchair,
    "stoly": draw_table,
    "krovati": draw_bed,
    "shkafy": draw_wardrobe,
    "polki": draw_shelf,
}


def _lighten(hex_color, factor=1.25):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_svg(slug, color, color2, furniture, label=""):
    bg1 = _lighten(color, 1.18)
    bg2 = color
    body = DRAW_FUNCS[furniture](color2)
    label_html = ""
    if label:
        label_html = (
            f'<rect x="180" y="536" width="440" height="44" rx="22" fill="rgba(255,255,255,0.16)"/>'
            f'<text x="400" y="566" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" '
            f'font-size="22" font-weight="600" fill="#ffffff">{label}</text>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <defs>
    <linearGradient id="bg-{slug}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{bg1}"/>
      <stop offset="100%" stop-color="{bg2}"/>
    </linearGradient>
  </defs>
  <rect width="800" height="600" fill="url(#bg-{slug})"/>
  <g opacity="0.08">
    <circle cx="80" cy="80" r="6" fill="#fff"/><circle cx="240" cy="160" r="4" fill="#fff"/>
    <circle cx="520" cy="60" r="5" fill="#fff"/><circle cx="700" cy="140" r="6" fill="#fff"/>
    <circle cx="120" cy="420" r="4" fill="#fff"/><circle cx="660" cy="460" r="5" fill="#fff"/>
    <circle cx="380" cy="500" r="4" fill="#fff"/><circle cx="200" cy="260" r="5" fill="#fff"/>
    <circle cx="600" cy="240" r="4" fill="#fff"/><circle cx="460" cy="520" r="5" fill="#fff"/>
  </g>
  <g transform="translate(0 30)">{body}</g>
  {label_html}
</svg>'''
    return svg


def generate_images(app):
    img_dir = os.path.join(app.static_folder, "img")
    os.makedirs(img_dir, exist_ok=True)
    written = []
    for cat in CATEGORIES:
        furniture = cat["slug"]
        if furniture not in DRAW_FUNCS:
            furniture = "stoly"
        svg = generate_svg(cat["slug"], cat["color"], cat["color2"], furniture, cat["name"])
        path = os.path.join(img_dir, cat["image"])
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        written.append(cat["image"])
    for p in PRODUCTS:
        cat = next(c for c in CATEGORIES if c["slug"] == p["category"])
        furniture = cat["slug"]
        slug = slugify(p["name"])
        image = f"products/{slug}.jpg"
        if os.path.exists(os.path.join(img_dir, image)):
            continue
        svg = generate_svg(slug, cat["color"], cat["color2"], furniture, p["name"])
        image = f"{slug}.svg"
        with open(os.path.join(img_dir, image), "w", encoding="utf-8") as f:
            f.write(svg)
        written.append(image)
    return written


def ensure_db(app):
    db = connect_db(app)
    db.executescript(DB_SCHEMA)
    if query(db, "SELECT COUNT(*) FROM categories")[0][0] == 0:
        now = datetime.now()
        cur = db.cursor()
        for cat in CATEGORIES:
            cur.execute(
                "INSERT INTO categories (name, slug, description, image) VALUES (?, ?, ?, ?)",
                (cat["name"], cat["slug"], cat["description"], cat["image"]),
            )
        for p in PRODUCTS:
            cat_id = cur.execute("SELECT id FROM categories WHERE slug = ?",
                                 (p["category"],)).fetchone()[0]
            slug = slugify(p["name"])
            created = now - timedelta(days=len(PRODUCTS) - PRODUCTS.index(p))
            cur.execute(
                "INSERT INTO products (category_id, name, slug, description, material, dimensions, "
                "warranty, price, old_price, stock, is_featured, image, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    cat_id, p["name"], slug, p["description"], p["material"],
                    p["dimensions"], p["warranty"], p["price"], p.get("old_price"),
                    p["stock"], p.get("featured", 0), f"products/{slug}.jpg",
                    created.isoformat(timespec="seconds"),
                ),
            )
        db.commit()
    for p in PRODUCTS:
        slug = slugify(p["name"])
        cur = db.execute("UPDATE products SET image = ? WHERE slug = ?",
                         (f"products/{slug}.jpg", slug))
    db.commit()
    generate_images(app)
    db.close()