from flask import Flask, render_template, request, session, redirect, url_for, flash
import requests
from datetime import datetime
from collections import Counter

app = Flask(__name__)
app.secret_key = "inbeauty_secret_key"

BASE_URL = "https://dummyjson.com/products"
ADMIN_KEY = "ADMIN123"

LOGS = []
CART_LOGS = []

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

# ================= HOME =================
@app.route("/")
def index():
    query = request.args.get("search", "")
    sort = request.args.get("sort", "")

    products = get_products()

    if query:
        products = [p for p in products if query.lower() in p["title"].lower()]

    if sort == "price_asc":
        products.sort(key=lambda x: x["price"])
    elif sort == "price_desc":
        products.sort(key=lambda x: x["price"], reverse=True)

    return render_template("index.html", products=products)

# ================= DETAIL =================
@app.route("/product/<int:id>")
def detail(id):
    product = get_product(id)

    LOGS.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product": product["title"],
        "ip": request.remote_addr,
        "browser": request.headers.get("User-Agent")[:40]
    })

    return render_template("detail.html", product=product)

# ================= CART =================
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

    CART_LOGS.append(product["title"])
    session["cart"] = cart
    flash("Produk berhasil masuk ke keranjang ✅")

    return redirect(request.referrer or "/")

@app.route("/cart")
def cart():
    cart_items = session.get("cart", [])
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    return render_template("cart.html", cart=cart_items, total=total)

@app.route("/remove-cart/<int:id>")
def remove_cart(id):
    cart_items = session.get("cart", [])
    cart_items = [item for item in cart_items if item["id"] != id]
    session["cart"] = cart_items
    return redirect(url_for("cart"))

# ================= ADMIN LOGS (PAKAI KEY) =================
@app.route("/admin/logs")
def admin_logs():
    key = request.args.get("key")
    if key != ADMIN_KEY:
        return "Forbidden: Invalid admin key", 403

    return render_template("admin/logs.html", logs=LOGS)

# ================= ADMIN STATISTICS (TANPA KEY) =================
@app.route("/admin/stats")
def admin_stats():
    view_counter = Counter(log["product"] for log in LOGS)
    cart_counter = Counter(CART_LOGS)

    return render_template(
        "admin/stats.html",
        total_logs=len(LOGS),
        view_stats=view_counter.most_common(5),
        cart_stats=cart_counter.most_common(5)
    )

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
