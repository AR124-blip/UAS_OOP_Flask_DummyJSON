from flask import Flask, render_template, request, session, redirect, url_for, flash
import requests
from datetime import datetime
from collections import Counter

app = Flask(__name__)
app.secret_key = "inbeauty_secret_key"

BASE_URL = "https://dummyjson.com/products"
LOGS = []

ALLOWED_CATEGORIES = [
    "beauty",
    "fragrances",
    "womens-dresses",
    "womens-shoes",
    "womens-watches",
    "womens-bags",
    "womens-jewellery",
]


def get_products():
    res = requests.get(f"{BASE_URL}?limit=100")
    products = res.json()["products"]
    return [p for p in products if p["category"] in ALLOWED_CATEGORIES]


def get_product(product_id):
    return requests.get(f"{BASE_URL}/{product_id}").json()


@app.route("/")
def index():
    query = request.args.get("search", "")
    products = get_products()

    if query:
        products = [p for p in products if query.lower() in p["title"].lower()]

    return render_template("index.html", products=products)


@app.route("/product/<int:id>")
def detail(id):
    product = get_product(id)

    # LOG VIEW PRODUCT
    LOGS.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": "VIEW PRODUCT",
        "product": product["title"],
        "ip": request.remote_addr,
        "browser": request.headers.get("User-Agent")[:40]
    })

    return render_template("detail.html", product=product)


@app.route("/add-to-cart/<int:id>")
def add_to_cart(id):
    product = get_product(id)
    cart = session.get("cart", [])

    for item in cart:
        if item["id"] == id:
            item["quantity"] += 1
            break
    else:
        cart.append({
            "id": id,
            "title": product["title"],
            "price": product["price"],
            "thumbnail": product["thumbnail"],
            "quantity": 1
        })

    session["cart"] = cart

    # LOG ADD TO CART
    LOGS.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": "ADD TO CART",
        "product": product["title"],
        "ip": request.remote_addr,
        "browser": request.headers.get("User-Agent")[:40]
    })

    flash("Produk berhasil masuk ke keranjang ✅")
    return redirect(request.referrer or "/")


@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] * item["quantity"] for item in cart)
    return render_template("cart.html", cart=cart, total=total)


@app.route("/remove-cart/<int:id>")
def remove_cart(id):
    cart = session.get("cart", [])
    cart = [item for item in cart if item["id"] != id]
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/admin/logs")
def admin_logs():
    return render_template("admin/logs.html", logs=LOGS)

@app.route("/admin/stats")
def admin_stats():
    view_counter = Counter()
    cart_counter = Counter()

    for log in LOGS:
        if log["action"] == "VIEW PRODUCT":
            view_counter[log["product"]] += 1
        elif log["action"] == "ADD TO CART":
            cart_counter[log["product"]] += 1

    return render_template(
        "admin/stats.html",
        view_stats=view_counter.most_common(5),
        cart_stats=cart_counter.most_common(5),
        total_logs=len(LOGS)
    )


if __name__ == "__main__":
    app.run(debug=True)
