from datetime import datetime
from db import get_connection


def import_price_snapshot_manual():
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        print("\n=== Import Price Snapshot ===")

        cursor.execute(
            """
            SELECT SecurityID, Ticker, Exchange, SecType, Currency
            FROM security
            ORDER BY SecurityID
            """
        )
        securities = cursor.fetchall()

        if not securities:
            print("No securities exist yet. Create some securities first.")
            return

        print("\nAvailable securities:")
        for sid, ticker, exch, sec_type, curr in securities:
            print(f"  ID={sid} | {ticker} ({sec_type}) on {exch} [{curr}]")

        sec_choice = input("\nEnter SecurityID for the snapshot (or press Enter to cancel): ").strip()
        if sec_choice == "":
            print("Cancelled.")
            return

        try:
            security_id = int(sec_choice)
        except ValueError:
            print("Invalid SecurityID.")
            return

        valid_ids = {row[0] for row in securities}
        if security_id not in valid_ids:
            print("That SecurityID is not in the list.")
            return

        date_str = input("Snapshot date (YYYY-MM-DD, blank = today): ").strip()
        if date_str == "":
            date_str = datetime.today().strftime("%Y-%m-%d")

        try:
            snapshot_time = datetime.strptime(date_str + " 16:00:00", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("Invalid date format.")
            return

        try:
            open_price = float(input("Open price: ").strip())
            high_price = float(input("High price: ").strip())
            low_price  = float(input("Low price: ").strip())
            close_price = float(input("Close price: ").strip())
        except ValueError:
            print("One of the price inputs was invalid.")
            return

        try:
            volume = int(input("Volume (integer): ").strip())
        except ValueError:
            print("Invalid volume.")
            return

        source = "Manual"
        interval_code = "1D"

        sql = """
            INSERT INTO price_snapshot
                (SecurityID, SnapshotTime, OpenPrice, HighPrice, LowPrice, ClosePrice,
                 Volume, Source, IntervalCode)
            VALUES
                (%s, %s, %s, %s, %s, %s,
                 %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                OpenPrice   = VALUES(OpenPrice),
                HighPrice   = VALUES(HighPrice),
                LowPrice    = VALUES(LowPrice),
                ClosePrice  = VALUES(ClosePrice),
                Volume      = VALUES(Volume),
                Source      = VALUES(Source),
                IntervalCode= VALUES(IntervalCode);
        """

        cursor.execute(
            sql,
            (
                security_id,
                snapshot_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                source,
                interval_code,
            )
        )
        conn.commit()

        print(f"\n✅ Price snapshot saved for SecurityID={security_id} at {snapshot_time}.")

    except Exception as e:
        print(f"[ERROR] Failed to import price snapshot: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
