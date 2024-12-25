const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const csv = require('csv-parser');
const jwt = require('jsonwebtoken'); // For JWT token generation

const app = express();
const port = process.env.PORT || 3000;
const secretKey = 'BelleCroissantSecret'; // Replace with a stronger secret in production

app.use(cors());
app.use(bodyParser.json());

// Read CSV files into arrays
let products = [];
let customers = [];
let orders = [];
let orderItems = [];

// Load CSV data 
fs.createReadStream('./products_cleaned.csv')
  .pipe(csv())
  .on('data', (row) => {
    products.push(row);
  })
  .on('end', () => {
    console.log('Products loaded:', products.length);
  });

fs.createReadStream('./customers_cleaned.csv')
  .pipe(csv())
  .on('data', (row) => {
    customers.push(row);
  })
  .on('end', () => {
    console.log('Customers loaded:', customers.length);
  });

fs.createReadStream('./sales_transactions_cleaned.csv')
  .pipe(csv())
  .on('data', (row) => {
    orders.push({
      OrderId: row.transaction_id,
      CustomerId: row.customer_id,
      OrderDate: `${row.date}T${row.time}`, // Combine date and time
      TotalAmount: (parseFloat(row.price) * parseInt(row.quantity)) - parseFloat(row.discount_amount || 0),
      Status: "Completed", 
      PaymentMethod: row.payment_method,
      Channel: row.channel,
      StoreId: row.store_id || null // Convert empty strings to null for online orders
    });

    orderItems.push({
      OrderItemId: row.transaction_id, 
      OrderId: row.transaction_id,
      ProductId: row.product_id,
      Quantity: row.quantity,
      Price: row.price,
    });
  })
  .on('end', () => {
    console.log('Orders loaded:', orders.length);
    console.log('Order items loaded:', orderItems.length);
  });

  // --- API Endpoints ---
// Authentication
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;

    // Check credentials (replace with your actual authentication logic)
    if (username === 'staff' && password === 'BCLyon2024') {
        const token = jwt.sign({ userId: username }, secretKey, { expiresIn: '1h' }); 
        res.json({ token });
    } else {
        res.status(401).send('Invalid credentials');
    }
});

// Middleware to verify JWT token for protected routes
app.use((req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1]; // Get token from header

    if (!token) {
        return res.status(401).send('Access denied. No token provided.');
    }

    try {
        const decoded = jwt.verify(token, secretKey);
        req.userId = decoded.userId;
        next();
    } catch (err) {
        res.status(400).send('Invalid token.');
    }
});

// Products
app.get('/api/products', (req, res) => {
    let filteredProducts = products;
    if (req.query.category) {
        filteredProducts = filteredProducts.filter(p => p.Category === req.query.category);
    }
    if (req.query.seasonal) {
        const seasonalValue = req.query.seasonal.toLowerCase() === 'true';
        filteredProducts = filteredProducts.filter(p => p.Seasonal === seasonalValue);
    }
    if (req.query.active) {
        const activeValue = req.query.active.toLowerCase() === 'true';
        filteredProducts = filteredProducts.filter(p => p.Active === activeValue);
    }
    if (req.query.sortBy) {
        const sortOrder = req.query.sortOrder === 'desc' ? -1 : 1;
        filteredProducts.sort((a, b) => (a[req.query.sortBy] > b[req.query.sortBy]) ? sortOrder : -sortOrder);
    }
    res.json(filteredProducts);
});

app.get('/api/products/:id', (req, res) => {
    const product = products.find(p => p.ProductId === req.params.id);
    if (product) {
        res.json(product);
    } else {
        res.status(404).send('Product not found');
    }
});

// POST /api/products (Create a new product)
app.post('/api/products', (req, res) => {
    const newProduct = req.body;

    // Basic data validation (add more as needed)
    if (!newProduct.ProductName || !newProduct.Category || !newProduct.Price) {
        return res.status(400).send('Missing required fields');
    }
    if (newProduct.Price <= 0 || newProduct.Cost <= 0 || newProduct.StockLevel < 0) {
        return res.status(400).send('Invalid values for price, cost, or stock level');
    }

    // Assign a new ID (assuming auto-increment is not used in the CSV)
    newProduct.ProductId = Math.max(...products.map(p => parseInt(p.ProductId))) + 1; 

    products.push(newProduct);
    res.status(201).json(newProduct); // 201 Created
});

// PUT /api/products/:id (Update an existing product)
app.put('/api/products/:id', (req, res) => {
    const productId = req.params.id;
    const updatedProduct = req.body;

    // Data validation (same as POST)
    // ...

    const index = products.findIndex(p => p.ProductId === productId);
    if (index !== -1) {
        products[index] = updatedProduct; // Replace with updated data
        res.json(updatedProduct);
    } else {
        res.status(404).send('Product not found');
    }
});

// DELETE /api/products/:id (Delete a product)
app.delete('/api/products/:id', (req, res) => {
    const productId = req.params.id;
    const index = products.findIndex(p => p.ProductId === productId);
    if (index !== -1) {
        const deletedProduct = products.splice(index, 1);
        res.json(deletedProduct[0]); // Return the deleted product
    } else {
        res.status(404).send('Product not found');
    }
});

// Customers
app.get('/api/customers', (req, res) => {
    let filteredCustomers = customers;
    if (req.query.membershipStatus) {
        filteredCustomers = filteredCustomers.filter(c => c.MembershipStatus === req.query.membershipStatus);
    }
    if (req.query.churned) {
        const churnedValue = req.query.churned.toLowerCase() === 'true';
        filteredCustomers = filteredCustomers.filter(c => c.churned === churnedValue);
    }
    if (req.query.sortBy) {
        const sortOrder = req.query.sortOrder === 'desc' ? -1 : 1;
        filteredCustomers.sort((a, b) => (a[req.query.sortBy] > b[req.query.sortBy]) ? sortOrder : -sortOrder);
    }
    res.json(filteredCustomers);
});

app.get('/api/customers/:id', (req, res) => {
    const customer = customers.find(c => c.customer_id === req.params.id);
    if (customer) {
        res.json(customer);
    } else {
        res.status(404).send('Customer not found');
    }
});

app.post('/api/customers', (req, res) => {
    const newCustomer = req.body;
    // Basic data validation (add more as needed)
    if (!newCustomer.first_name || !newCustomer.last_name || !newCustomer.email) {
        return res.status(400).send('Missing required fields');
    }
    
    // Assign a new ID (assuming auto-increment is not used in the CSV)
    newCustomer.customer_id = Math.max(...customers.map(c => parseInt(c.customer_id))) + 1; 
    
    customers.push(newCustomer);
    res.status(201).json(newCustomer);
});

app.put('/api/customers/:id', (req, res) => {
    const customerId = req.params.id;
    const updatedCustomer = req.body;

    // Data validation (same as POST)
    // ...

    const index = customers.findIndex(c => c.customer_id === customerId);
    if (index !== -1) {
        customers[index] = updatedCustomer;
        res.json(updatedCustomer);
    } else {
        res.status(404).send('Customer not found');
    }
});

// Orders Endpoints
app.get('/api/orders', (req, res) => {
    let filteredOrders = orders;
    if (req.query.customerId) {
        filteredOrders = filteredOrders.filter(o => o.CustomerId === req.query.customerId);
    }
    if (req.query.status) {
        filteredOrders = filteredOrders.filter(o => o.Status === req.query.status);
    }
    if (req.query.startDate || req.query.endDate) {
        const startDate = new Date(req.query.startDate || '1900-01-01'); 
        const endDate = new Date(req.query.endDate || Date.now());
        filteredOrders = filteredOrders.filter(o => {
            const orderDate = new Date(o.OrderDate);
            return orderDate >= startDate && orderDate <= endDate;
        });
    }
    if (req.query.sortBy) {
        const sortOrder = req.query.sortOrder === 'desc' ? -1 : 1;
        filteredOrders.sort((a, b) => (a[req.query.sortBy] > b[req.query.sortBy]) ? sortOrder : -sortOrder);
    }

    const ordersWithItems = filteredOrders.map(order => {
        const items = orderItems.filter(item => item.OrderId === order.OrderId);
        return { ...order, items };
    });

    res.json(ordersWithItems);
});

app.get('/api/orders/:id', (req, res) => {
    const order = orders.find(o => o.order_id === req.params.id);
    if (order) {
        const items = orderItems.filter(i => i.order_id === req.params.id);
        res.json({ ...order, items }); // Include order items in response
    } else {
        res.status(404).send('Order not found');
    }
});

app.post('/api/orders', (req, res) => {
    const newOrder = req.body;
    // Basic data validation (add more as needed)
    if (!newOrder.customer_id || !Array.isArray(newOrder.items) || newOrder.items.length === 0) {
        return res.status(400).send('Missing required fields or invalid items');
    }

    // Assign a new ID
    newOrder.order_id = Math.max(...orders.map(o => parseInt(o.order_id))) + 1;

    // Add order items (adjust as per your data structure)
    newOrder.items.forEach(item => {
        orderItems.push({
            order_item_id: Math.max(...orderItems.map(i => parseInt(i.order_item_id))) + 1, 
            order_id: newOrder.order_id,
            product_id: item.product_id,
            quantity: item.quantity,
            price: item.price,
        });
    });
    
    orders.push(newOrder);
    res.status(201).json(newOrder);
});
// GET /api/orders/:id (Retrieve details of a specific order by ID)
app.get('/api/orders/:id', (req, res) => {
    const orderId = req.params.id;
    const order = orders.find(o => o.OrderId === orderId);
    if (order) {
        const items = orderItems.filter(i => i.OrderId === orderId);
        res.json({ ...order, items });
    } else {
        res.status(404).send('Order not found');
    }
});

// POST /api/orders (Create a new order)
app.post('/api/orders', (req, res) => {
    const newOrder = req.body;

    // Basic data validation
    if (!newOrder.CustomerId || !Array.isArray(newOrder.items) || newOrder.items.length === 0) {
        return res.status(400).send('Missing required fields or invalid items');
    }

    // Check if customer exists
    const customer = customers.find(c => c.customer_id === newOrder.CustomerId);
    if (!customer) {
        return res.status(400).send('Invalid customer ID');
    }

    // Check if products exist and have enough stock
    for (const item of newOrder.items) {
        const product = products.find(p => p.ProductId === item.ProductId);
        if (!product || product.Active === 'FALSE' || parseInt(product.StockLevel) < parseInt(item.Quantity)) {
            return res.status(400).send('Invalid product ID or insufficient stock');
        }
    }
   

    // Assign a new ID (assuming auto-increment is not used in the CSV)
    newOrder.OrderId = Math.max(...orders.map(o => parseInt(o.OrderId))) + 1;
    newOrder.Status = "Pending"; // Set initial status to pending
    newOrder.OrderDate = new Date().toISOString();

    // Add order items
    newOrder.items.forEach(item => {
        orderItems.push({
            OrderItemId: Math.max(...orderItems.map(i => parseInt(i.OrderItemId))) + 1,
            OrderId: newOrder.OrderId,
            ProductId: item.ProductId,
            Quantity: item.Quantity,
            Price: parseFloat(item.Price)
        });
    });

    orders.push(newOrder);
    res.status(201).json(newOrder);
});

// PUT /api/orders/{id}/complete (Mark an order as completed)
app.put('/api/orders/:id/complete', (req, res) => {
    const orderId = req.params.id;
    const index = orders.findIndex(o => o.OrderId === orderId);
    if (index !== -1) {
        if (orders[index].Status === 'Pending' || orders[index].Status === 'Processing') { // Check if order is pending or processing
            orders[index].Status = 'Completed';
            res.json(orders[index]);
        } else {
            res.status(400).send('Invalid order status. Order cannot be completed.');
        }
    } else {
        res.status(404).send('Order not found');
    }
});

// PUT /api/orders/{id}/cancel (Mark an order as canceled)
app.put('/api/orders/:id/cancel', (req, res) => {
    const orderId = req.params.id;
    const index = orders.findIndex(o => o.OrderId === orderId);
    if (index !== -1) {
        if (orders[index].Status === 'Pending' || orders[index].Status === 'Processing') {
            orders[index].Status = 'Cancelled';
            res.json(orders[index]);
        } else {
            res.status(400).send('Invalid order status. Order cannot be cancelled.');
        }
    } else {
        res.status(404).send('Order not found');
    }
});

// Authentication (Basic Authentication)
// ... (Same as before, with 'staff' and 'BCLyon2024')

app.listen(port, () => {
  console.log(`Belle Croissant Lyonnais API listening on port ${port}`);
});
