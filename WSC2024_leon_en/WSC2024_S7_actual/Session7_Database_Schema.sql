CREATE DATABASE BelleCroissantLyonnaisBI;
GO

USE BelleCroissantLyonnaisBI;
GO

-- Customers Table (Added)
CREATE TABLE Customers (
    CustomerId INT PRIMARY KEY, -- No Identity, we'll use IDs from the main database
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Age INT NULL CHECK (Age >= 0),
    Gender NVARCHAR(1) NULL CHECK (Gender IN ('M', 'F', 'O')),
    PostalCode NVARCHAR(10) NULL,
    Email NVARCHAR(100) UNIQUE,
    PhoneNumber NVARCHAR(20) NULL,
    MembershipStatus NVARCHAR(20) NOT NULL DEFAULT 'Basic',
    JoinDate DATE NULL,
    LastPurchaseDate DATE NULL
);

-- CustomerFeedback Table
CREATE TABLE CustomerFeedback (
    FeedbackId INT PRIMARY KEY IDENTITY(1,1),
    CustomerId INT NOT NULL, -- Foreign key to Customers table
    Rating INT NOT NULL CHECK (Rating BETWEEN 1 AND 5),
    Comment NVARCHAR(MAX) NULL,
    DateSubmitted DATETIME2 NOT NULL DEFAULT GETDATE()
);

-- SocialMediaEngagement Table
CREATE TABLE SocialMediaEngagement (
    EngagementId INT PRIMARY KEY IDENTITY(1,1),
    Platform NVARCHAR(50) NOT NULL, -- 'Facebook', 'Instagram', 'Twitter', etc.
    PostType NVARCHAR(50) NOT NULL, -- 'Post', 'Story', 'Reel', etc.
    Reach INT NOT NULL CHECK (Reach >= 0),
    Impressions INT NOT NULL CHECK (Impressions >= 0),
    EngagementCount INT NOT NULL CHECK (EngagementCount >= 0),
    Date DATE NOT NULL
);

-- WebsiteAnalytics Table
CREATE TABLE WebsiteAnalytics (
    AnalyticsId INT PRIMARY KEY IDENTITY(1,1),
    Date DATE NOT NULL,
    PageViews INT NOT NULL CHECK (PageViews >= 0),
    UniqueVisitors INT NOT NULL CHECK (UniqueVisitors >= 0),
    BounceRate DECIMAL(5,2) NOT NULL CHECK (BounceRate BETWEEN 0 AND 100),
    AverageSessionDuration TIME NULL 
);

-- LoyaltyProgramHistory Table
CREATE TABLE LoyaltyProgramHistory (
    HistoryId INT PRIMARY KEY IDENTITY(1,1),
    CustomerId INT NOT NULL, 
    Action NVARCHAR(50) NOT NULL CHECK (Action IN ('Points Earned', 'Points Redeemed', 'Tier Upgrade')),
    Points INT NOT NULL,
    Timestamp DATETIME2 NOT NULL DEFAULT GETDATE()
);
GO
