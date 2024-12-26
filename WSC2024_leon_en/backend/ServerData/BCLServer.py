import csv
from flask import Flask, request, jsonify, make_response
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
from copy import deepcopy
from datetime import datetime, timedelta
import uuid
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=48)  # 48-hour token expiration
jwt = JWTManager(app)

# Data file paths
PRODUCTS_FILE = 'products_cleaned.csv'
CUSTOMERS_FILE = 'customers_cleaned.csv'
ORDERS_FILE = 'sales_transactions_cleaned.csv'

# Store session data
sessions = {}

# Function to load CSV data with improved error handling
def load_csv(filename):
    data = []
    encodings = ['utf-8', 'ISO-8859-1']
    
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as file:
                csv_reader = csv.DictReader(file)
                data = list(csv_reader)
            break  # If successful, break out of the loop
        except UnicodeDecodeError:
            continue  # If unsuccessful, try the next encoding
    
    if not data:
        app.logger.error(f"Unable to decode the file {filename} with the attempted encodings.")
        raise ValueError(f"Unable to decode the file {filename} with the attempted encodings.")
    
    return data

# Load original data
original_products = load_csv(PRODUCTS_FILE)
original_customers = load_csv(CUSTOMERS_FILE)
original_orders = load_csv(ORDERS_FILE)

# Error handling
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized", "message": str(error)}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": str(error)}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

# Authentication
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if username != 'staff' or password != 'BCLyon2024':
        return jsonify({"error": "Bad username or password"}), 401

    # Create a new session with fresh data on login
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'products': deepcopy(original_products),
        'customers': deepcopy(original_customers),
        'orders': deepcopy(original_orders),
        'expiration': datetime.utcnow() + timedelta(hours=48)
    }

    # Create access token with 48-hour expiry
    access_token = create_access_token(identity=session_id)

    response = jsonify(access_token=access_token, session_id=session_id)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response, 200

# Helper function to get session data with expiration check
def get_session_data(session_id):
    if session_id not in sessions:
        return None

    session = sessions[session_id]
    if session['expiration'] < datetime.utcnow():
        # Session expired, remove it
        del sessions[session_id]
        return None

    return session

# XML serialization function
def dict_to_xml(tag, d):
    elem = ET.Element(tag)
    for key, val in d.items():
        child = ET.SubElement(elem, key)
        child.text = str(val)
    return elem

# Versioning and content negotiation
@app.route('/api/v1/products', methods=['GET'])
@jwt_required()
def get_products():
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
    
    accept = request.headers.get('Accept', 'application/json')
    if accept == 'application/xml':
        root = ET.Element('products')
        for product in session_data['products']:
            root.append(dict_to_xml('product', product))
        return app.response_class(ET.tostring(root), mimetype='application/xml')
    
    response = make_response(jsonify(session_data['products']))
    response.headers['Content-Type'] = 'application/json'
    response.headers['ETag'] = str(hash(str(session_data['products'])))
    return response, 200

@app.route('/api/v1/products/<int:id>', methods=['GET'])
@jwt_required()
def get_product(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
    
    product = next((p for p in session_data['products'] if int(p['product_id']) == id), None)
    if product:
        response = make_response(jsonify(product))
        response.headers['Content-Type'] = 'application/json'
        response.headers['ETag'] = str(hash(str(product)))
        return response, 200
    return jsonify({"error": "Product not found"}), 404

@app.route('/api/v1/products', methods=['POST'])
@jwt_required()
def add_product():
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
    
    new_product = request.json

    # Check for required fields
    if not all(k in new_product for k in ('product_name', 'category', 'price', 'cost')):
        return jsonify({"error": "Missing required fields"}), 400

    # Assign product_id
    new_product['product_id'] = str(max(int(p['product_id']) for p in session_data['products']) + 1)

    # Set introduced_date if not provided
    if 'introduced_date' not in new_product:
        new_product['introduced_date'] = datetime.now().strftime('%m/%d/%Y')

    # Set default values for optional fields if not provided
    new_product.setdefault('ingredients', '')
    new_product.setdefault('seasonal', 'FALSE')
    new_product.setdefault('active', 'TRUE')

    session_data['products'].append(new_product)
    response = make_response(jsonify(new_product))
    response.headers['Location'] = f"/api/v1/products/{new_product['product_id']}"
    return response, 201

@app.route('/api/v1/products/<int:id>', methods=['PUT'])
@jwt_required()
def update_product(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
    
    product = next((p for p in session_data['products'] if int(p['product_id']) == id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    product.update(request.json)
    return jsonify(product), 200

@app.route('/api/v1/products/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
    
    session_data['products'] = [p for p in session_data['products'] if int(p['product_id']) != id]
    return '', 204

# Get all customers
@app.route('/api/v1/customers', methods=['GET'])
@jwt_required()
def get_customers():
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    accept = request.headers.get('Accept', 'application/json')
    if accept == 'application/xml':
        root = ET.Element('customers')
        for customer in session_data['customers']:
            root.append(dict_to_xml('customer', customer))
        return app.response_class(ET.tostring(root), mimetype='application/xml')
   
    response = make_response(jsonify(session_data['customers']))
    response.headers['Content-Type'] = 'application/json'
    response.headers['ETag'] = str(hash(str(session_data['customers'])))
    return response, 200

# Get a specific customer
@app.route('/api/v1/customers/<int:id>', methods=['GET'])
@jwt_required()
def get_customer(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    customer = next((c for c in session_data['customers'] if int(c['customer_id']) == id), None)
    if customer:
        response = make_response(jsonify(customer))
        response.headers['Content-Type'] = 'application/json'
        response.headers['ETag'] = str(hash(str(customer)))
        return response, 200
    return jsonify({"error": "Customer not found"}), 404

# Add a new customer
@app.route('/api/v1/customers', methods=['POST'])
@jwt_required()
def add_customer():
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    new_customer = request.json

    # Check for required fields
    required_fields = ['first_name', 'last_name', 'email']
    if not all(k in new_customer for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Assign customer_id
    new_customer['customer_id'] = str(max(int(c['customer_id']) for c in session_data['customers']) + 1)

    # Set join_date if not provided
    if 'join_date' not in new_customer:
        new_customer['join_date'] = datetime.now().strftime('%m/%d/%Y')

    # Set default values for optional fields if not provided
    new_customer.setdefault('age', '')
    new_customer.setdefault('gender', '')
    new_customer.setdefault('postal_code', '')
    new_customer.setdefault('phone_number', '')
    new_customer.setdefault('membership_status', 'Basic')
    new_customer.setdefault('last_purchase_date', '')
    new_customer.setdefault('total_spending', '0')
    new_customer.setdefault('average_order_value', '0')
    new_customer.setdefault('frequency', '0')
    new_customer.setdefault('preferred_category', '')
    new_customer.setdefault('churned', 'FALSE')

    session_data['customers'].append(new_customer)
    response = make_response(jsonify(new_customer))
    response.headers['Location'] = f"/api/v1/customers/{new_customer['customer_id']}"
    return response, 201

# Update an existing customer
@app.route('/api/v1/customers/<int:id>', methods=['PUT'])
@jwt_required()
def update_customer(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    customer = next((c for c in session_data['customers'] if int(c['customer_id']) == id), None)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    customer.update(request.json)
    return jsonify(customer), 200

# Delete a customer
@app.route('/api/v1/customers/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_customer(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    session_data['customers'] = [c for c in session_data['customers'] if int(c['customer_id']) != id]
    return '', 204

# Get all orders
@app.route('/api/v1/orders', methods=['GET'])
@jwt_required()
def get_orders():
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    accept = request.headers.get('Accept', 'application/json')
    if accept == 'application/xml':
        root = ET.Element('orders')
        for order in session_data['orders']:
            root.append(dict_to_xml('order', order))
        return app.response_class(ET.tostring(root), mimetype='application/xml')
   
    response = make_response(jsonify(session_data['orders']))
    response.headers['Content-Type'] = 'application/json'
    response.headers['ETag'] = str(hash(str(session_data['orders'])))
    return response, 200

# Get a specific order
@app.route('/api/v1/orders/<int:id>', methods=['GET'])
@jwt_required()
def get_order(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    order = next((o for o in session_data['orders'] if int(o['transaction_id']) == id), None)
    if order:
        response = make_response(jsonify(order))
        response.headers['Content-Type'] = 'application/json'
        response.headers['ETag'] = str(hash(str(order)))
        return response, 200
    return jsonify({"error": "Order not found"}), 404

# Add a new order
@app.route('/api/v1/orders', methods=['POST'])
@jwt_required()
def add_order():
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    new_order = request.json

    # Check for required fields
    required_fields = ['customer_id', 'date', 'time', 'product_id', 'quantity', 'price', 'payment_method', 'channel']
    if not all(k in new_order for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Assign transaction_id
    new_order['transaction_id'] = str(max(int(o['transaction_id']) for o in session_data['orders']) + 1)

    # Set default values for optional fields if not provided
    new_order.setdefault('store_id', '')
    new_order.setdefault('promotion_id', '')
    new_order.setdefault('discount_amount', '0.0')

    session_data['orders'].append(new_order)
    response = make_response(jsonify(new_order))
    response.headers['Location'] = f"/api/v1/orders/{new_order['transaction_id']}"
    return response, 201

# Update an existing order
@app.route('/api/v1/orders/<int:id>', methods=['PUT'])
@jwt_required()
def update_order(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    order = next((o for o in session_data['orders'] if int(o['transaction_id']) == id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    order.update(request.json)
    return jsonify(order), 200

# Delete an order
@app.route('/api/v1/orders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_order(id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    session_data['orders'] = [o for o in session_data['orders'] if int(o['transaction_id']) != id]
    return '', 204

# Get orders for a specific customer
@app.route('/api/v1/customers/<int:customer_id>/orders', methods=['GET'])
@jwt_required()
def get_customer_orders(customer_id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    customer_orders = [o for o in session_data['orders'] if int(o['customer_id']) == customer_id]
    
    if not customer_orders:
        return jsonify({"message": "No orders found for this customer"}), 404
    
    response = make_response(jsonify(customer_orders))
    response.headers['Content-Type'] = 'application/json'
    response.headers['ETag'] = str(hash(str(customer_orders)))
    return response, 200

# Get orders for a specific product
@app.route('/api/v1/products/<int:product_id>/orders', methods=['GET'])
@jwt_required()
def get_product_orders(product_id):
    session_id = get_jwt_identity()
    session_data = get_session_data(session_id)
   
    if not session_data:
        return jsonify({"error": "Invalid or expired session"}), 401
   
    product_orders = [o for o in session_data['orders'] if int(o['product_id']) == product_id]
    
    if not product_orders:
        return jsonify({"message": "No orders found for this product"}), 404
    
    response = make_response(jsonify(product_orders))
    response.headers['Content-Type'] = 'application/json'
    response.headers['ETag'] = str(hash(str(product_orders)))
    return response, 200

# Endpoint to reset session data
@app.route('/api/v1/reset', methods=['POST'])
@jwt_required()
def reset_session():
    session_id = get_jwt_identity()
    if session_id in sessions:
        sessions[session_id] = {
            'products': deepcopy(original_products),
            'customers': deepcopy(original_customers),
            'orders': deepcopy(original_orders),
            'expiration': datetime.utcnow() + timedelta(hours=48)
        }
        return jsonify({"message": "Session data reset successfully"}), 200
    return jsonify({"error": "Session not found"}), 404

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))