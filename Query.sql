CREATE DATABASE portfolio_db;
USE portfolio_db;

-- ================
-- USERS & PHONES
-- ================

CREATE TABLE IF NOT EXISTS app_user (
    UserID        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    PrimaryEmail  VARCHAR(255) NOT NULL UNIQUE,
    PasswordHash  VARCHAR(255) NOT NULL,
    CreatedAt     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Fname         VARCHAR(50)  NOT NULL,
    Mname         VARCHAR(50)  NULL,
    Lname         VARCHAR(50)  NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_phone (
  UserID      INT UNSIGNED NOT NULL,
  PhoneNumber VARCHAR(20)  NOT NULL,
  PRIMARY KEY (UserID, PhoneNumber),
  CONSTRAINT fk_user_phone_user
      FOREIGN KEY (UserID)
          REFERENCES app_user(UserID)
          ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =======================
-- BROKERAGE ACCOUNT
-- =======================

CREATE TABLE IF NOT EXISTS brokerage_account (
     AccountID      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
     AccountNumber  VARCHAR(50)  NOT NULL UNIQUE,
     AccountType    VARCHAR(30)  NOT NULL,    -- e.g. 'TAXABLE','IRA','ROTH'
     BrokerageName  VARCHAR(100) NOT NULL,
     BaseCurrency   CHAR(3)      NOT NULL,    -- e.g. 'USD'
     Nickname       VARCHAR(100) NULL,
     OwnerUserID    INT UNSIGNED NOT NULL,
     CONSTRAINT fk_brokerage_owner
         FOREIGN KEY (OwnerUserID)
             REFERENCES app_user(UserID)
             ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =======================
-- PORTFOLIO
-- =======================

CREATE TABLE IF NOT EXISTS portfolio (
     PortfolioID        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
     PortfolioName      VARCHAR(100) NOT NULL,
     BaseCurrency       CHAR(3)      NOT NULL,
     CreatedAt          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
     OwnerUserID        INT UNSIGNED NOT NULL,
     ManagedByAccountID INT UNSIGNED NULL,
     CONSTRAINT fk_portfolio_owner
         FOREIGN KEY (OwnerUserID)
             REFERENCES app_user(UserID)
             ON DELETE RESTRICT,
     CONSTRAINT fk_portfolio_account
         FOREIGN KEY (ManagedByAccountID)
             REFERENCES brokerage_account(AccountID)
             ON DELETE SET NULL,
     CONSTRAINT uq_portfolio_owner_name
         UNIQUE (OwnerUserID, PortfolioName)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =======================
-- SECURITY MASTER
-- =======================

CREATE TABLE IF NOT EXISTS security (
    SecurityID   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    Ticker       VARCHAR(16)  NOT NULL,
    Exchange     VARCHAR(50)  NOT NULL,
    Currency     CHAR(3)      NOT NULL,
    SecType      VARCHAR(30)  NOT NULL,  -- 'STOCK','ETF','BOND','CASH','CRYPTO','OTHER'
    Sector       VARCHAR(100) NULL,
    Industry     VARCHAR(100) NULL,
    CONSTRAINT uq_security_ticker_exchange
        UNIQUE (Ticker, Exchange)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =======================
-- SECURITY TAGS
-- =======================

CREATE TABLE IF NOT EXISTS security_tag (
    SecurityID INT UNSIGNED NOT NULL,
    Tag        VARCHAR(50)  NOT NULL,
    PRIMARY KEY (SecurityID, Tag),
    CONSTRAINT fk_security_tag_security
        FOREIGN KEY (SecurityID)
            REFERENCES security(SecurityID)
            ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =======================
-- TRADE / TRANSACTION
-- =======================

CREATE TABLE IF NOT EXISTS trade (
     TransactionID INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
     PortfolioID   INT UNSIGNED NOT NULL,
     SecurityID    INT UNSIGNED NULL,
     Type          VARCHAR(20)  NOT NULL,    -- 'BUY','SELL','DIVIDEND','CASH_DEPOSIT', etc.
     TradeDate     DATE         NOT NULL,
     SettleDate    DATE         NULL,
     Quantity      DECIMAL(18,4) NOT NULL,   -- usually > 0; meaning depends on Type
     UnitPrice     DECIMAL(18,4) NOT NULL,
     Fees          DECIMAL(18,4) NOT NULL DEFAULT 0,
     TradeCurrency CHAR(3)      NOT NULL,
     Notes         VARCHAR(500) NULL,
     CONSTRAINT fk_trade_portfolio
         FOREIGN KEY (PortfolioID)
             REFERENCES portfolio(PortfolioID)
             ON DELETE CASCADE,
     CONSTRAINT fk_trade_security
         FOREIGN KEY (SecurityID)
             REFERENCES security(SecurityID)
             ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =======================
-- HOLDING
-- =======================

CREATE TABLE IF NOT EXISTS holding (
   PortfolioID    INT UNSIGNED NOT NULL,
   SecurityID     INT UNSIGNED NOT NULL,
   AvgCostBasis   DECIMAL(18,4) NOT NULL DEFAULT 0,
   PRIMARY KEY (PortfolioID, SecurityID),
   CONSTRAINT fk_holding_portfolio
       FOREIGN KEY (PortfolioID)
           REFERENCES portfolio(PortfolioID)
           ON DELETE CASCADE,
   CONSTRAINT fk_holding_security
       FOREIGN KEY (SecurityID)
           REFERENCES security(SecurityID)
           ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =======================
-- PRICE SNAPSHOT
-- =======================

CREATE TABLE IF NOT EXISTS price_snapshot (
  SecurityID    INT UNSIGNED NOT NULL,
  SnapshotTime  DATETIME     NOT NULL,
  OpenPrice     DECIMAL(18,4) NOT NULL,
  HighPrice     DECIMAL(18,4) NOT NULL,
  LowPrice      DECIMAL(18,4) NOT NULL,
  ClosePrice    DECIMAL(18,4) NOT NULL,
  Volume        BIGINT       NOT NULL,
  Source        VARCHAR(50)  NOT NULL,
  IntervalCode  VARCHAR(20)  NOT NULL,  -- '1D','1H','1MIN', etc.
  PRIMARY KEY (SecurityID, SnapshotTime),
  CONSTRAINT fk_price_snapshot_security
      FOREIGN KEY (SecurityID)
          REFERENCES security(SecurityID)
          ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


