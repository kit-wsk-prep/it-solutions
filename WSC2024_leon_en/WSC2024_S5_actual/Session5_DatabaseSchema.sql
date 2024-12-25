
USE BelleCroissantLyonnais;
GO

-- Promotions Table
CREATE TABLE Promotions (
    PromotionId INT PRIMARY KEY IDENTITY(1,1),
    PromotionName NVARCHAR(100) NOT NULL,
    DiscountType NVARCHAR(20) NOT NULL CHECK (DiscountType IN ('Percentage', 'FixedAmount')),
    DiscountValue DECIMAL(10, 2) NOT NULL CHECK (DiscountValue > 0),
    ApplicableProducts NVARCHAR(MAX) NULL, -- Comma-separated list of product IDs
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    MinimumOrderValue DECIMAL(10, 2) NULL CHECK (MinimumOrderValue >= 0),
    Priority INT NOT NULL DEFAULT 0, -- Priority for conflict resolution
    QuantityBasedRules NVARCHAR(MAX) NULL -- JSON structure for quantity-based discounts
);

-- QuantityBasedRuleDetails Table (Separate Table for Quantity-Based Rules)
CREATE TABLE QuantityBasedRuleDetails (
    RuleId INT PRIMARY KEY IDENTITY(1,1),
    PromotionId INT,
    MinQuantity INT NOT NULL CHECK (MinQuantity > 0),
    DiscountValue DECIMAL(10, 2) NOT NULL CHECK (DiscountValue > 0),
    FOREIGN KEY (PromotionId) REFERENCES Promotions(PromotionId)
);

-- LoyaltyProgram Table
CREATE TABLE LoyaltyProgram (
    CustomerId INT PRIMARY KEY,
    Points INT NOT NULL DEFAULT 0 CHECK (Points >= 0),
    MembershipTier NVARCHAR(20) NOT NULL DEFAULT 'Basic'
);
GO
