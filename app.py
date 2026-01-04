from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime

app = Flask(__name__)

class InBeautyService:
    def __init__(self):
        self.base_url = "https://dummyjson.com/products"
        self.access_logs = []

    def get_filtered_products(self, search_query=None):
        response = requests.get(f"{self.base_url}?limit=100")
        all_products = response.json().get('products', [])
        
        allowed_categories = [
            'beauty', 'fragrances', 'womens-dresses', 
            'womens-shoes', 'womens-watches', 'womens-bags', 'womens-jewellery'
        ]
        
        filtered = [p for p in all_products if p['category'] in allowed_categories]
        
        if search_query:
            filtered = [p for p in filtered if search_query.lower() in p['title'].lower()]
            
        return filtered

    def get_detail(self, product_id):
        response = requests.get(f"{self.base_url}/{product_id}")
        product = response.json()
        
        user_info = {
            "product_name": product.get('title'),
            "ip": request.remote_addr,
            "browser": request.headers.get('User-Agent')[:50],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.access_logs.insert(0, user_info)
        return product

service = InBeautyService()

@app.route('/')
def index():
    query = request.args.get('search')
    products = service.get_filtered_products(query)
    return render_template('index.html', products=products)

@app.route('/product/<int:id>')
def detail(id):
    product = service.get_detail(id)
    return render_template('detail.html', product=product, logs=service.access_logs)

@app.route('/admin/logs')
def admin_logs():
    return render_template('admin.html', logs=service.access_logs)

if __name__ == '__main__':
    app.run(debug=True)