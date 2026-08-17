import os
from datetime import datetime

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for

import seed

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "furniture-shop-dev-secret")
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30

_initialized = False


@app.before_request
def ensure_ready():
    global _initialized
    if not _initialized:
        seed.ensure_db(app)
        _initialized = True


@app.template_filter("money")
def money(value):
    try:
        return f"{int(value):,}".replace(",", " ") + " ₽"
    except (TypeError, ValueError):
        return "—"


@app.template_filter("date_ru")
def date_ru(value):
    if not value:
        return ""
    return value.strftime("%d.%m.%Y")


@app.template_filter("plural_ru")
def plural_ru(n, one="товар", few="товара", many="товаров"):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return one
    abs_n = abs(n) % 100
    last = abs_n % 10
    if 11 <= abs_n <= 14:
        return many
    if last == 1:
        return one
    if 2 <= last <= 4:
        return few
    return many


def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = seed.connect_db(app)
    return db


@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


def cart_contents():
    cart = session.get("cart", {})
    items = []
    total = 0
    for product_id, qty in cart.items():
        product = seed.get_product(get_db(), int(product_id))
        if product is None or qty <= 0:
            continue
        subtotal = product["price"] * qty
        total += subtotal
        items.append({**product, "qty": qty, "subtotal": subtotal})
    return items, total


def cart_count():
    return sum(qty for qty in session.get("cart", {}).values() if qty > 0)


@app.context_processor
def inject_globals():
    return {
        "categories": seed.get_categories(get_db()),
        "cart_count": cart_count(),
        "current_year": datetime.now().year,
    }


# ---------- Pages ----------


@app.route("/")
def index():
    db = get_db()
    featured = seed.get_products(db, featured=True, limit=8)
    new_arrivals = seed.get_products(db, order_by="new", limit=8)
    return render_template(
        "index.html",
        featured=featured,
        new_arrivals=new_arrivals,
    )


@app.route("/catalog")
def catalog():
    db = get_db()
    category_slug = request.args.get("category", "")
    sort = request.args.get("sort", "popular")
    q = request.args.get("q", "").strip()
    price_min = request.args.get("min", "").strip()
    price_max = request.args.get("max", "").strip()
    in_stock = request.args.get("in_stock") == "1"

    products = seed.search_products(
        db,
        category=category_slug,
        search=q,
        sort=sort,
        price_min=int(price_min) if price_min.isdigit() else None,
        price_max=int(price_max) if price_max.isdigit() else None,
        in_stock_only=in_stock,
    )
    return render_template(
        "catalog.html",
        products=products,
        active_category=category_slug,
        sort=sort,
        q=q,
        price_min=price_min,
        price_max=price_max,
        in_stock=in_stock,
        total=len(products),
    )


@app.route("/catalog/<slug>")
def category(slug):
    db = get_db()
    category = seed.get_category_by_slug(db, slug)
    if category is None:
        abort(404)
    products = seed.get_products(db, category_id=category["id"])
    return render_template(
        "catalog.html",
        products=products,
        active_category=slug,
        sort="popular",
        q="",
        price_min="",
        price_max="",
        in_stock=False,
        total=len(products),
        category_title=category["name"],
    )


@app.route("/product/<slug>")
def product(slug):
    db = get_db()
    product = seed.get_product_by_slug(db, slug)
    if product is None:
        abort(404)
    related = seed.get_products(
        db, category_id=product["category_id"], exclude_id=product["id"], limit=4
    )
    return render_template("product.html", product=product, related=related)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        flash("Спасибо! Ваше сообщение отправлено — мы ответим в течение рабочего дня.", "success")
        return redirect(url_for("contacts"))
    return render_template("contacts.html")


# ---------- Cart ----------


@app.route("/cart")
def cart():
    items, total = cart_contents()
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/add/<int:product_id>")
def cart_add(product_id):
    db = get_db()
    product = seed.get_product(db, product_id)
    if product is None:
        abort(404)
    qty = 1
    try:
        qty = max(1, min(int(request.form.get("qty", 1)), 99))
    except ValueError:
        qty = 1
    cart = dict(session.get("cart", {}))
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session["cart"] = cart
    if request.headers.get("X-Requested-With") == "fetch":
        return {"ok": True, "cart_count": cart_count()}
    next_url = request.form.get("next") or request.referrer or url_for("cart")
    return redirect(next_url)


@app.post("/cart/update/<int:product_id>")
def cart_update(product_id):
    try:
        qty = max(0, min(int(request.form.get("qty", 1)), 99))
    except ValueError:
        qty = 0
    cart = dict(session.get("cart", {}))
    if qty == 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = qty
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:product_id>")
def cart_remove(product_id):
    cart = dict(session.get("cart", {}))
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/checkout")
def checkout():
    items, total = cart_contents()
    if not items:
        return redirect(url_for("catalog"))
    return render_template("checkout.html", items=items, total=total)


@app.post("/checkout")
def checkout_submit():
    items, total = cart_contents()
    if not items:
        return redirect(url_for("catalog"))

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    comment = request.form.get("comment", "").strip()
    payment = request.form.get("payment", "cash")

    if not name or not phone or not address:
        flash("Пожалуйста, заполните имя, телефон и адрес доставки.", "error")
        return render_template("checkout.html", items=items, total=total)

    db = get_db()
    order_id = seed.create_order(
        db,
        name=name,
        phone=phone,
        email=email,
        address=address,
        comment=comment,
        payment=payment,
        total=total,
        items=[{"product_id": i["id"], "name": i["name"], "price": i["price"], "qty": i["qty"]} for i in items],
    )
    session["cart"] = {}
    return redirect(url_for("order_success", order_id=order_id))


@app.route("/order/<int:order_id>")
def order_success(order_id):
    db = get_db()
    order = seed.get_order(db, order_id)
    if order is None:
        abort(404)
    return render_template("order_success.html", order=order)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    import socket

    with app.app_context():
        seed.ensure_db(app)

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")

    if debug and host not in ("127.0.0.1", "localhost"):
        print("Внимание: режим DEBUG включён — доступен только с этого компьютера.")
        host = "127.0.0.1"

    print("\nFurnio запущен!")
    print("  Локально:     http://127.0.0.1:%d" % port)
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                print("  В сети:       http://%s:%d  (покажите этот адрес другим)" % (ip, port))
    except socket.gaierror:
        pass
    print("  Остановка:    Ctrl+C\n")

    app.run(host=host, port=port, debug=debug)