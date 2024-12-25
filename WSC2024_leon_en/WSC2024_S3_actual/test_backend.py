from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# In-memory storage
products = []
orders = []

# File paths for persistence
PRODUCTS_FILE = 'products.json'
ORDERS_FILE = 'orders.json'

def load_data():
    global products, orders
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r') as f:
            orders = json.load(f)

def save_data():
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f)
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f)

def validate_product(data):
    errors = {}
    if 'name' not in data or not isinstance(data['name'], str):
        errors['name'] = 'Name is required and must be a string'
    if 'price' not in data or not isinstance(data['price'], (int, float)) or data['price'] < 0:
        errors['price'] = 'Price is required and must be a non-negative number'
    if 'stock' not in data or not isinstance(data['stock'], int) or data['stock'] < 0:
        errors['stock'] = 'Stock is required and must be a non-negative integer'
    return errors

def validate_order(data):
    errors = {}
    if 'product_id' not in data or not isinstance(data['product_id'], int):
        errors['product_id'] = 'Product ID is required and must be an integer'
    if 'quantity' not in data or not isinstance(data['quantity'], int) or data['quantity'] <= 0:
        errors['quantity'] = 'Quantity is required and must be a positive integer'
    return errors

# Routes for Products
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({"message": "Product not found"}), 404

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    errors = validate_product(data)
    if errors:
        return jsonify(errors), 400
    product = {
        'id': len(products) + 1,
        'name': data['name'],
        'price': data['price'],
        'stock': data['stock']
    }
    products.append(product)
    save_data()
    return jsonify(product), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    data = request.json
    errors = validate_product(data)
    if errors:
        return jsonify(errors), 400
    product.update(data)
    save_data()
    return jsonify(product)

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    global products
    products = [p for p in products if p['id'] != product_id]
    save_data()
    return '', 204

# Routes for Orders
@app.route('/api/orders', methods=['GET'])
def get_orders():
    return jsonify(orders)

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = next((o for o in orders if o['id'] == order_id), None)
    if order:
        return jsonify(order)
    return jsonify({"message": "Order not found"}), 404

@app.route('/api/orders', methods=['POST'])
def add_order():
    data = request.json
    errors = validate_order(data)
    if errors:
        return jsonify(errors), 400
    product = next((p for p in products if p['id'] == data['product_id']), None)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    if product['stock'] < data['quantity']:
        return jsonify({"message": "Not enough stock"}), 400
    order = {
        'id': len(orders) + 1,
        'product_id': data['product_id'],
        'quantity': data['quantity'],
        'total_price': product['price'] * data['quantity']
    }
    product['stock'] -= data['quantity']
    orders.append(order)
    save_data()
    return jsonify(order), 201

@app.route('/api/orders/<int:order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return jsonify({"message": "Order not found"}), 404
    # Here you could add logic for marking an order as complete, e.g., updating status
    save_data()
    return jsonify(order)

@app.route('/api/orders/<int:order_id>/cancel', methods=['PUT'])
def cancel_order(order_id):
    global orders
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return jsonify({"message": "Order not found"}), 404
    product = next((p for p in products if p['id'] == order['product_id']), None)
    if product:
        product['stock'] += order['quantity']  # Return stock to inventory
    orders = [o for o in orders if o['id'] != order_id]
    save_data()
    return '', 204

if __name__ == '__main__':
    load_data()
if __name__ == '__main__':
    load_data()
    app.run(debug=True, port=3000)