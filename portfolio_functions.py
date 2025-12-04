# portfolio_functions.py

from typing import Optional
from db import get_connection


def _choose_user_portfolio(current_user_id: int) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.PortfolioID,
                   p.PortfolioName,
                   p.BaseCurrency,
                   p.ManagedByAccountID,
                   b.AccountNumber,
                   b.BrokerageName
            FROM portfolio p
            LEFT JOIN brokerage_account b
                ON p.ManagedByAccountID = b.AccountID
            WHERE p.OwnerUserID = %s
            ORDER BY p.PortfolioID
            """,
            (current_user_id,)
        )
        rows = cursor.fetchall()

        if not rows:
            print("\nYou don't have any portfolios yet.")
            print("Please create a portfolio first.")
            return None

        print("\nYour portfolios:")
        for pid, pname, curr, acc_id, acct_num, broker_name in rows:
            if acc_id is None:
                acc_label = "Unlinked"
            else:
                acc_label = f"{broker_name} (Acct #{acct_num}, ID={acc_id})"
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


def _choose_or_create_brokerage_account(current_user_id: int) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT AccountID, AccountNumber, AccountType, BrokerageName, BaseCurrency, Nickname
            FROM brokerage_account
            WHERE OwnerUserID = %s
            ORDER BY AccountID
            """,
            (current_user_id,)
        )
        rows = cursor.fetchall()

        print("\nBrokerage accounts:")
        if not rows:
            print("  (You don't have any brokerage accounts yet.)")
        else:
            for acc_id, acct_num, acc_type, broker_name, base_curr, nickname in rows:
                nick_str = f" '{nickname}'" if nickname else ""
                print(
                    f"  ID={acc_id} | {broker_name}{nick_str} "
                    f"(Acct #{acct_num}, Type={acc_type}, Cur={base_curr})"
                )

        print("\nOptions:")
        print("  1. Link to an existing brokerage account")
        print("  2. Create a new brokerage account")
        print("  3. Leave portfolio unlinked to any account")
        choice = input("Enter choice (1/2/3): ").strip()

        if choice == "3":
            return None

        if choice == "1":
            if not rows:
                print("You don't have any accounts yet; you must create one.")
            else:
                acc_choice = input("Enter AccountID of the account to link: ").strip()
                try:
                    acc_id = int(acc_choice)
                except ValueError:
                    print("Invalid AccountID.")
                    return None

                valid_ids = {r[0] for r in rows}
                if acc_id not in valid_ids:
                    print("That AccountID is not one of your accounts.")
                    return None

                return acc_id

        print("\n=== Create New Brokerage Account ===")
        account_number = input("Brokerage account number (any ID you like): ").strip()
        account_type = input("Account type (e.g. TAXABLE, IRA, ROTH): ").strip() or "TAXABLE"
        brokerage_name = input("Brokerage name (e.g. Robinhood, Fidelity): ").strip()
        base_currency = input("Base currency (e.g. USD): ").strip() or "USD"
        nickname = input("Nickname (optional): ").strip() or None

        insert_sql = """
            INSERT INTO brokerage_account
                (AccountNumber, AccountType, BrokerageName, BaseCurrency, Nickname, OwnerUserID)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_sql,
            (account_number, account_type, brokerage_name, base_currency, nickname, current_user_id)
        )
        conn.commit()
        new_id = cursor.lastrowid
        print(f"Created brokerage account ID={new_id} at {brokerage_name}.")
        return new_id

    except Exception as e:
        print(f"[ERROR] Failed to choose/create brokerage account: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def create_portfolio(current_user_id: int):
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        print("\n=== Create New Portfolio ===")
        name = input("Portfolio name: ").strip()
        if not name:
            print("Portfolio name is required.")
            return

        base_currency = input("Base currency (e.g. USD): ").strip() or "USD"

        account_id = _choose_or_create_brokerage_account(current_user_id)

        insert_sql = """
            INSERT INTO portfolio
                (PortfolioName, BaseCurrency, OwnerUserID, ManagedByAccountID)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            insert_sql,
            (name, base_currency, current_user_id, account_id)
        )
        conn.commit()
        pid = cursor.lastrowid

        if account_id is None:
            print(f"Portfolio '{name}' created with ID={pid} (not linked to any brokerage account).")
        else:
            print(f"Portfolio '{name}' created with ID={pid} and linked to BrokerageAccountID={account_id}.")

    except Exception as e:
        print(f"[ERROR] Failed to create portfolio: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def move_portfolio_to_account(current_user_id: int):
    portfolio_id = _choose_user_portfolio(current_user_id)
    if portfolio_id is None:
        return

    account_id = _choose_or_create_brokerage_account(current_user_id)

    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE portfolio
            SET ManagedByAccountID = %s
            WHERE PortfolioID = %s
              AND OwnerUserID = %s
            """,
            (account_id, portfolio_id, current_user_id)
        )
        conn.commit()

        pname = _load_portfolio_name_for_move(portfolio_id)

        if account_id is None:
            print(f"Portfolio '{pname}' (ID={portfolio_id}) is now UNLINKED from any brokerage account.")
        else:
            print(f"Portfolio '{pname}' (ID={portfolio_id}) is now linked to BrokerageAccountID={account_id}.")

    except Exception as e:
        print(f"[ERROR] Failed to move portfolio to another account: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def _load_portfolio_name_for_move(portfolio_id: int) -> str:
    conn = get_connection()
    if conn is None:
        return f"Portfolio {portfolio_id}"

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT PortfolioName FROM portfolio WHERE PortfolioID = %s",
            (portfolio_id,)
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        return f"Portfolio {portfolio_id}"
    except Exception:
        return f"Portfolio {portfolio_id}"
    finally:
        cursor.close()
        conn.close()
