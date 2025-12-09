# Portfolio Manager Application

## Overview
The Portfolio Manager is a command-line Python application backed by a MySQL relational database.  
It allows a user to manage investment portfolios, record trades, track holdings, import price snapshots, and view performance metrics.  

---

## Project Structure
- main.py
- db.py
- portfolio_function.py
- trade_functions.py
- snapshot_functions.py
- tag_functions.py
- Query.sql
- db_config.json

## Requirements
- Python 3.10 or higher
- MYSQL Server (localhost)
- MySQL client such as MySQL Workbench or DataGrip
- **Required Python Package**
  -   ```pip install mysql-connector-python```
   
## Database Setup
1. Open MySQL using your preferred client.
2. Create the database manually:
   - ```CREATE DATABASE portfolio_db;```
   - ```USE portfolio_db``` 
3. Run ```query.sql``` to create all tables
This creates all the required tables:
- Users
- Brokerage accounts
- Portfolios
- Securities + tags
- Trades
- Holdings
- Price snapshots

## Running the Application
From the project directory:
- ```main.py```
You will be presented with an authentication menu to:
- Log in
- Create a new user
After logging in, the main menu provides:
1. Create Portfolio
  - Creates a new investment portfolio and optionally links it to a brokerage account.
2. Record Trade (Buy/Sell)
  - Allows the user to enter BUY or SELL transactions.
  - Trades update positions and are later used to calculate holdings.
3. Record Dividend
  - Records cash dividends. These do not affect share quantity but are recorded in the trade history.
4. Import Price Snapshot
  - Stores Open, High, Low, Close, and Volume data for a security.
  - These values determine market value when viewing portfolio performance.
5. Show Portfolio Snapshot Value
  - Displays:
    - Total invested amount
    - Total market value based on the latest snapshots
    - Unrealized profit/loss
    - Per-security:
    - Ticker
    - Shares
    - Average cost
    - Last close price
    - Market value
    - Unrealized P/L
6. View Holdings Report
  - Recalculates holdings based on all BUY and SELL trades.
  - Shows BuyQty, SellQty, NetQty, and Average Cost Basis.
7. View Trade History by Security
  - Displays all recorded trades (BUY, SELL, DIVIDEND) for a chosen security.
8. Move Portfolio to Another Brokerage Account
  - Updates the portfolio's linked brokerage account.
9. Add Security Tag
  - Adds tags such as "Tech", "Dividend", "Speculative", etc.
  - A security may have many tags.
