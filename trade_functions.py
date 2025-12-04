from datetime import datetime
from typing import Optional

from db import get_connection
from security_functions import create_security


def _choose_portfolio(current_user_id: int) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT PortfolioID, PortfolioName, BaseCurrency, ManagedByAccountID
            FROM portfolio
            WHERE OwnerUserID = %s
            ORDER BY PortfolioID
            """,
            (current_user_id,)
        )
        rows = cursor.fetchall()

        if not rows:
            print("\nYou don't have any portfolios yet.")
            print("Please create a portfolio first.")
            return None

        print("\nYour portfolios:")
        for pid, pname, curr, acc_id in rows:
            acc_label = f"AccountID={acc_id}" if acc_id is not None else "Unlinked"
            print(f"  ID={pid} | {pname} ({curr}) - {acc_label}")

        choice = input("\nEnter PortfolioID to use (or press Enter to cancel): ").strip()
        if choice == "":
            print("Cancelled.")
            return None

        try:
            chosen_id = int(choice)
        except ValueError:
            print("Invalid PortfolioID.")
            return None

        valid_ids = {row[0] for row in rows}
        if chosen_id not in valid_ids:
            print("That PortfolioID is not one of your portfolios.")
            return None

        return chosen_id

    except Exception as e:
        print(f"[ERROR] Failed to list portfolios: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def _choose_security() -> Optional[int]:
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT SecurityID, Ticker, Exchange, SecType, Currency
            FROM security
            ORDER BY SecurityID
            """
        )
        rows = cursor.fetchall()

        print("\nAvailable securities:")
        if not rows:
            print("  (none yet)")
        else:
            for sid, ticker, exch, sec_type, curr in rows:
                print(f"  ID={sid} | {ticker} ({sec_type}) on {exch} [{curr}]")

        print("\nChoose a security:")
        print("  Enter an existing SecurityID")
        print("  N = create a new security")
        print("  Enter nothing to cancel")

        choice = input("Choice: ").strip()
        if choice == "":
            print("Cancelled.")
            return None

        if choice.lower() == "n":
            sec_id = create_security()
            return sec_id

        try:
            chosen_id = int(choice)
        except ValueError:
            print("Invalid SecurityID.")
            return None

        valid_ids = {row[0] for row in rows}
        if chosen_id not in valid_ids:
            print("That SecurityID is not in the list.")
            return None

        return chosen_id

    except Exception as e:
        print(f"[ERROR] Failed to list securities: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def record_trade(current_user_id: int):
    # 1. Pick portfolio
    portfolio_id = _choose_portfolio(current_user_id)
    if portfolio_id is None:
        return

    # 2. Pick security
    security_id = _choose_security()
    if security_id is None:
        return

    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        print("\n=== Record Trade (BUY/SELL) ===")
        trade_type = input("Trade type (BUY or SELL): ").strip().upper()
        if trade_type not in ("BUY", "SELL"):
            print("Trade type must be BUY or SELL.")
            return

        date_str = input("Trade date (YYYY-MM-DD, blank = today): ").strip()
        if date_str == "":
            trade_date = datetime.today().date()
        else:
            try:
                trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date format.")
                return

        settle_str = input("Settle date (YYYY-MM-DD, blank = same as trade): ").strip()
        if settle_str == "":
            settle_date = trade_date
        else:
            try:
                settle_date = datetime.strptime(settle_str, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date format.")
                return

        try:
            qty = float(input("Quantity (e.g. 10.5): ").strip())
        except ValueError:
            print("Invalid quantity.")
            return

        try:
            price = float(input("Unit price (e.g. 150.25): ").strip())
        except ValueError:
            print("Invalid price.")
            return

        fees_str = input("Fees (blank = 0): ").strip()
        if fees_str == "":
            fees = 0.0
        else:
            try:
                fees = float(fees_str)
            except ValueError:
                print("Invalid fees.")
                return

        # Use the security's currency as the trade currency
        cursor.execute(
            "SELECT Currency FROM security WHERE SecurityID = %s",
            (security_id,)
        )
        sec_row = cursor.fetchone()
        if not sec_row:
            print("[ERROR] Security disappeared, aborting.")
            return
        trade_currency = sec_row[0]

        sql = """
            INSERT INTO trade
                (PortfolioID, SecurityID, Type, TradeDate, SettleDate,
                 Quantity, UnitPrice, Fees, TradeCurrency, Notes)
            VALUES
                (%s, %s, %s, %s, %s,
                 %s, %s, %s, %s, %s)
        """
        notes = input("Notes (optional): ").strip() or None

        cursor.execute(
            sql,
            (
                portfolio_id,
                security_id,
                trade_type,
                trade_date,
                settle_date,
                qty,
                price,
                fees,
                trade_currency,
                notes,
            ),
        )
        conn.commit()

        print("\n✅ Trade recorded successfully.")

    except Exception as e:
        print(f"[ERROR] Failed to record trade: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def record_dividend(current_user_id: int):
    # 1. Pick portfolio
    portfolio_id = _choose_portfolio(current_user_id)
    if portfolio_id is None:
        return

    # 2. Pick security
    security_id = _choose_security()
    if security_id is None:
        return

    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        print("\n=== Record Dividend ===")
        # Type is always DIVIDEND
        trade_type = "DIVIDEND"

        date_str = input("Dividend date (YYYY-MM-DD, blank = today): ").strip()
        if date_str == "":
            trade_date = datetime.today().date()
        else:
            try:
                trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date format.")
                return

        settle_str = input("Pay date (YYYY-MM-DD, blank = same as dividend date): ").strip()
        if settle_str == "":
            settle_date = trade_date
        else:
            try:
                settle_date = datetime.strptime(settle_str, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date format.")
                return

        print("\nWe will store:")
        print("- Quantity      = number of shares receiving the dividend")
        print("- UnitPrice     = dividend amount per share")
        print("- Total cash    = Quantity * UnitPrice (can be computed later in reports)\n")

        try:
            qty = float(input("Number of shares this dividend applies to (e.g. 15): ").strip())
        except ValueError:
            print("Invalid quantity.")
            return

        try:
            div_per_share = float(input("Dividend per share (e.g. 0.25): ").strip())
        except ValueError:
            print("Invalid dividend amount.")
            return

        fees_str = input("Fees/withholding tax (blank = 0): ").strip()
        if fees_str == "":
            fees = 0.0
        else:
            try:
                fees = float(fees_str)
            except ValueError:
                print("Invalid fees.")
                return

        # Use the security's currency as the trade currency
        cursor.execute(
            "SELECT Currency FROM security WHERE SecurityID = %s",
            (security_id,)
        )
        sec_row = cursor.fetchone()
        if not sec_row:
            print("[ERROR] Security disappeared, aborting.")
            return
        trade_currency = sec_row[0]

        notes = input("Notes (optional): ").strip() or None

        sql = """
            INSERT INTO trade
                (PortfolioID, SecurityID, Type, TradeDate, SettleDate,
                 Quantity, UnitPrice, Fees, TradeCurrency, Notes)
            VALUES
                (%s, %s, %s, %s, %s,
                 %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                portfolio_id,
                security_id,
                trade_type,
                trade_date,
                settle_date,
                qty,
                div_per_share,
                fees,
                trade_currency,
                notes,
            )
        )
        conn.commit()

        print("\n✅ Dividend recorded successfully.")

    except Exception as e:
        print(f"[ERROR] Failed to record dividend: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def trade_history_by_security(current_user_id: int):
    # 1. Pick portfolio
    portfolio_id = _choose_portfolio(current_user_id)
    if portfolio_id is None:
        return

    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        # Find distinct securities traded in this portfolio
        cursor.execute(
            """
            SELECT DISTINCT s.SecurityID, s.Ticker, s.Exchange, s.SecType, s.Currency
            FROM trade t
            JOIN security s ON t.SecurityID = s.SecurityID
            WHERE t.PortfolioID = %s
            ORDER BY s.SecurityID
            """,
            (portfolio_id,)
        )
        sec_rows = cursor.fetchall()

        if not sec_rows:
            print("\nNo trades recorded for this portfolio yet.")
            return

        print("\nSecurities traded in this portfolio:")
        for sid, ticker, exch, sec_type, curr in sec_rows:
            print(f"  ID={sid} | {ticker} ({sec_type}) on {exch} [{curr}]")

        choice = input("\nEnter SecurityID to view trade history (or press Enter to cancel): ").strip()
        if choice == "":
            print("Cancelled.")
            return

        try:
            security_id = int(choice)
        except ValueError:
            print("Invalid SecurityID.")
            return

        valid_ids = {row[0] for row in sec_rows}
        if security_id not in valid_ids:
            print("That SecurityID is not in the traded list for this portfolio.")
            return

        # Fetch trades for that (portfolio, security)
        cursor.execute(
            """
            SELECT
                t.TransactionID,
                t.Type,
                t.TradeDate,
                t.SettleDate,
                t.Quantity,
                t.UnitPrice,
                t.Fees,
                t.TradeCurrency,
                t.Notes
            FROM trade t
            WHERE t.PortfolioID = %s
              AND t.SecurityID = %s
            ORDER BY t.TradeDate, t.TransactionID
            """,
            (portfolio_id, security_id)
        )
        trades = cursor.fetchall()

        if not trades:
            print("\nNo trades found for that security in this portfolio.")
            return

        print("\n=== Trade History ===")
        for (
            txn_id,
            ttype,
            tdate,
            sdate,
            qty,
            uprice,
            fees,
            curr,
            notes,
        ) in trades:
            print("---------------------------------------")
            print(f"TransactionID : {txn_id}")
            print(f"Type          : {ttype}")
            print(f"TradeDate     : {tdate}")
            print(f"SettleDate    : {sdate}")
            print(f"Quantity      : {qty}")
            print(f"UnitPrice     : {uprice} {curr}")
            print(f"Fees          : {fees} {curr}")
            if ttype == "DIVIDEND":
                total_div = (qty or 0) * (uprice or 0)
                print(f"Total Dividend: {total_div} {curr}")
            if notes:
                print(f"Notes         : {notes}")

        print("---------------------------------------")
        print("✅ End of trade history.")

    except Exception as e:
        print(f"[ERROR] Failed to show trade history: {e}")
    finally:
        cursor.close()
        conn.close()
