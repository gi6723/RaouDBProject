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
2. Run the SQL schema file
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
2. Record Trade (Buy/Sell)
3. Record dividend
4. Import Price snapshot
5. Show portfolio value
6. View holdings report
7. View Trade history by security
8. Move portfolio to another brokerage account
9. Add security tag to a security
