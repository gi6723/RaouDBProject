from typing import Optional
from db import get_connection


def create_security() -> Optional[int]:
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return None

    try:
        cursor = conn.cursor()

        print("\n=== Create New Security ===")
        ticker = input("Ticker (e.g. AAPL): ").strip().upper()
        if not ticker:
            print("Ticker is required.")
            return None

        exchange = input("Exchange (e.g. NASDAQ, NYSE, CRYPTO): ").strip().upper()
        if not exchange:
            exchange = "UNKNOWN"

        currency = input("Trading currency (e.g. USD): ").strip().upper() or "USD"
        sec_type = input("Security type (STOCK, ETF, BOND, CRYPTO, OTHER): ").strip().upper() or "STOCK"
        sector = input("Sector (optional): ").strip() or None
        industry = input("Industry (optional): ").strip() or None

        sql = """
            INSERT INTO security (Ticker, Exchange, Currency, SecType, Sector, Industry)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (ticker, exchange, currency, sec_type, sector, industry))
        conn.commit()

        sec_id = cursor.lastrowid
        print(f"\n✅ Security created with SecurityID={sec_id} ({ticker} on {exchange}).")
        return sec_id

    except Exception as e:
        print(f"[ERROR] Failed to create security: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def add_security_tag(current_user_id: int):
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        # Show existing securities
        cursor.execute(
            """
            SELECT SecurityID, Ticker, Exchange, SecType, Currency
            FROM security
            ORDER BY SecurityID
            """
        )
        securities = cursor.fetchall()

        print("\n=== Add Security Tag ===")
        if not securities:
            print("No securities exist yet.")
            create_choice = input("Create a new security now? (Y/N): ").strip().lower()
            if create_choice != "y":
                print("No security selected. Aborting.")
                return

            sec_id = create_security()
            if sec_id is None:
                print("Failed to create security. Aborting.")
                return
        else:
            print("Existing securities:")
            for sid, ticker, exch, sec_type, curr in securities:
                print(f"  ID={sid} | {ticker} ({sec_type}) on {exch} [{curr}]")

            choice = input("\nEnter SecurityID to tag, or N to create a new one: ").strip()

            if choice.lower() == "n":
                sec_id = create_security()
                if sec_id is None:
                    print("Failed to create security. Aborting.")
                    return
            else:
                try:
                    sec_id_candidate = int(choice)
                except ValueError:
                    print("Invalid SecurityID. Aborting.")
                    return

                valid_ids = {row[0] for row in securities}
                if sec_id_candidate not in valid_ids:
                    print("That SecurityID is not in the list. Aborting.")
                    return
                sec_id = sec_id_candidate

        # Ask for tag
        tag = input("Enter tag label (e.g. Tech, Dividend, Speculative): ").strip()
        if not tag:
            print("Tag cannot be empty. Aborting.")
            return

        insert_tag_sql = """
            INSERT INTO security_tag (SecurityID, Tag)
            VALUES (%s, %s)
        """
        try:
            cursor.execute(insert_tag_sql, (sec_id, tag))
            conn.commit()
            print(f"\n✅ Tag '{tag}' added to SecurityID={sec_id}.")
        except Exception as e:
            # Likely duplicate PK violation if tag already exists for that security
            print(f"[ERROR] Failed to add tag (maybe it already exists?): {e}")
            conn.rollback()

    finally:
        cursor.close()
        conn.close()
