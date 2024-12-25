CREATE DATABASE BelleCroissantLyonnais;
GO

USE BelleCroissantLyonnais;
GO

CREATE TABLE Products (
    ProductId INT PRIMARY KEY IDENTITY(1,1),
    ProductName NVARCHAR(100) NOT NULL,
    Category NVARCHAR(50) NOT NULL,
    Price DECIMAL(10, 2) NOT NULL CHECK (Price >= 0),
    Cost DECIMAL(10, 2) NOT NULL CHECK (Cost >= 0),
    Description NVARCHAR(MAX) NULL,
    Seasonal BIT NOT NULL,
    Active BIT NOT NULL,
    IntroducedDate DATE NOT NULL,
    Ingredients NVARCHAR(MAX) NULL
);

CREATE TABLE Customers (
    CustomerId INT PRIMARY KEY IDENTITY(1,1),
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Age INT NULL CHECK (Age >= 0),
    Gender NVARCHAR(1) NULL CHECK (Gender IN ('M', 'F', 'O')),
    PostalCode NVARCHAR(10) NULL,
    Email NVARCHAR(100) UNIQUE,
    PhoneNumber NVARCHAR(20) NULL,
    MembershipStatus NVARCHAR(20) NOT NULL DEFAULT 'Basic',
    JoinDate DATE NULL,
    LastPurchaseDate DATE NULL,
    TotalSpending DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (TotalSpending >= 0),
    AverageOrderValue DECIMAL(10, 2) NULL,
    Frequency NVARCHAR(50) NULL,
    PreferredCategory NVARCHAR(50) NULL,
    Churned BIT NULL
);

CREATE TABLE Orders (
    TransactionId INT PRIMARY KEY IDENTITY(1,1),
    CustomerId INT NOT NULL,
    OrderDate DATETIME NOT NULL,
    TotalAmount DECIMAL(10, 2) NOT NULL CHECK (TotalAmount >= 0),
    Status NVARCHAR(20) NOT NULL DEFAULT 'Pending', -- Pending, Processing, Completed, Cancelled
    PaymentMethod NVARCHAR(50) NOT NULL,
    Channel NVARCHAR(20) NOT NULL, -- In-store, Online
    StoreId INT NULL,
    PromotionId INT NULL,
    DiscountAmount DECIMAL(10, 2) NULL,
    CONSTRAINT FK_Orders_Customers FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId)
);

CREATE TABLE OrderItems (
    OrderItemId INT PRIMARY KEY IDENTITY(1,1),
    TransactionId INT NOT NULL,
    ProductId INT NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    Price DECIMAL(10, 2) NOT NULL CHECK (Price >= 0),
    CONSTRAINT FK_OrderItems_Orders FOREIGN KEY (TransactionId) REFERENCES Orders(TransactionId),
    CONSTRAINT FK_OrderItems_Products FOREIGN KEY (ProductId) REFERENCES Products(ProductId)
);
GO

-- Note: After data import, consider adding indexes for performance optimization:
-- CREATE INDEX idx_CustomerId ON Orders(CustomerId);
-- CREATE INDEX idx_ProductId ON OrderItems(ProductId);
-- Add more indexes as necessary based on query patterns.