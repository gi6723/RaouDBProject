from typing import Optional

from db import get_connection


def _choose_portfolio(current_user_id: int) -> Optional[int]:
    """
    Helper: list this user's portfolios and let them choose one by ID.
    Shows linked brokerage name/nickname instead of just AccountID.
    """
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                p.PortfolioID,
                p.PortfolioName,
                p.BaseCurrency,
                p.ManagedByAccountID,
                b.BrokerageName,
                b.AccountNumber,
                b.Nickname
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
        for pid, pname, curr, acc_id, broker_name, acct_num, nickname in rows:
            if acc_id is None:
                acc_label = "Unlinked"
            else:
                nick_str = f" '{nickname}'" if nickname else ""
                acc_label = f"{broker_name}{nick_str} (Acct #{acct_num}, ID={acc_id})"

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


def _load_portfolio_name(portfolio_id: int) -> str:
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


def _rebuild_holdings_for_portfolio(portfolio_id: int):
    """
    Rebuilds holding table for this portfolio based on BUY trades.
    """
    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database to rebuild holdings.")
        return

    try:
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM holding WHERE PortfolioID = %s",
            (portfolio_id,)
        )

        cursor.execute(
            """
            SELECT
                t.SecurityID,
                SUM(CASE WHEN t.Type = 'BUY' THEN t.Quantity ELSE 0 END) AS BuyQty,
                SUM(CASE WHEN t.Type = 'BUY'
                         THEN (t.Quantity * t.UnitPrice + t.Fees)
                         ELSE 0 END) AS TotalBuyCost
            FROM trade t
            WHERE t.PortfolioID = %s
              AND t.Type IN ('BUY','SELL')
            GROUP BY t.SecurityID
            """,
            (portfolio_id,)
        )
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO holding (PortfolioID, SecurityID, AvgCostBasis)
            VALUES (%s, %s, %s)
        """

        for security_id, buy_qty, total_buy_cost in rows:
            buy_qty = float(buy_qty or 0)
            if buy_qty <= 0:
                continue

            total_buy_cost = float(total_buy_cost or 0.0)
            avg_cost_basis = total_buy_cost / buy_qty
            cursor.execute(insert_sql, (portfolio_id, security_id, avg_cost_basis))

        conn.commit()
        print("[INFO] Holding table refreshed for this portfolio based on trades.")

    except Exception as e:
        print(f"[ERROR] Failed to rebuild holdings table: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def holdings_report(current_user_id: int):
    portfolio_id = _choose_portfolio(current_user_id)
    if portfolio_id is None:
        return

    _rebuild_holdings_for_portfolio(portfolio_id)

    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                s.SecurityID,
                s.Ticker,
                s.SecType,
                SUM(CASE WHEN t.Type = 'BUY'  THEN t.Quantity ELSE 0 END) AS BuyQty,
                SUM(CASE WHEN t.Type = 'SELL' THEN t.Quantity ELSE 0 END) AS SellQty,
                SUM(CASE WHEN t.Type = 'BUY'
                         THEN (t.Quantity * t.UnitPrice + t.Fees)
                         ELSE 0 END) AS TotalBuyCost
            FROM trade t
            JOIN security s ON t.SecurityID = s.SecurityID
            WHERE t.PortfolioID = %s
              AND t.Type IN ('BUY','SELL')
            GROUP BY s.SecurityID, s.Ticker, s.SecType
            """,
            (portfolio_id,)
        )
        rows = cursor.fetchall()

        holdings = []
        for sid, ticker, sec_type, buy_qty, sell_qty, total_buy_cost in rows:
            buy_qty = float(buy_qty or 0)
            sell_qty = float(sell_qty or 0)
            total_buy_cost = float(total_buy_cost or 0.0)

            net_qty = buy_qty - sell_qty
            if net_qty == 0:
                continue

            avg_cost_per_share = None
            if buy_qty > 0:
                avg_cost_per_share = total_buy_cost / buy_qty

            holdings.append(
                (sid, ticker, sec_type, buy_qty, sell_qty, net_qty, avg_cost_per_share)
            )

        if not holdings:
            print("\nNo open positions (net quantity) found for this portfolio.")
            return

        pname = _load_portfolio_name(portfolio_id)
        print(f"\n=== Holdings Report for {pname} (ID={portfolio_id}) ===")
        print(f"{'Ticker':<8} {'Type':<8} {'BuyQty':>8} {'SellQty':>8} {'NetQty':>8} {'AvgCost':>12}")
        print("-" * 60)

        for sid, ticker, sec_type, buy_qty, sell_qty, net_qty, avg_cost in holdings:
            avg_cost_str = f"{avg_cost:.2f}" if avg_cost is not None else "N/A"
            print(f"{ticker:<8} {sec_type:<8} {buy_qty:>8.2f} {sell_qty:>8.2f} {net_qty:>8.2f} {avg_cost_str:>12}")

        print("-" * 60)
        print("End of holdings report.")

    except Exception as e:
        print(f"[ERROR] Failed to generate holdings report: {e}")
    finally:
        cursor.close()
        conn.close()


def portfolio_snapshot_value(current_user_id: int):

    portfolio_id = _choose_portfolio(current_user_id)
    if portfolio_id is None:
        return

    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        # 1) Aggregate trades into positions
        cursor.execute(
            """
            SELECT
                s.SecurityID,
                s.Ticker,
                s.SecType,
                SUM(CASE WHEN t.Type = 'BUY'  THEN t.Quantity ELSE 0 END) AS BuyQty,
                SUM(CASE WHEN t.Type = 'SELL' THEN t.Quantity ELSE 0 END) AS SellQty,
                SUM(CASE WHEN t.Type = 'BUY'
                         THEN (t.Quantity * t.UnitPrice + t.Fees)
                         ELSE 0 END) AS TotalBuyCost
            FROM trade t
            JOIN security s ON t.SecurityID = s.SecurityID
            WHERE t.PortfolioID = %s
              AND t.Type IN ('BUY','SELL')
            GROUP BY s.SecurityID, s.Ticker, s.SecType
            """,
            (portfolio_id,)
        )
        rows = cursor.fetchall()

        holdings = []
        for sid, ticker, sec_type, buy_qty, sell_qty, total_buy_cost in rows:
            buy_qty = float(buy_qty or 0)
            sell_qty = float(sell_qty or 0)
            total_buy_cost = float(total_buy_cost or 0.0)

            net_qty = buy_qty - sell_qty
            if net_qty <= 0:
                # no open position
                continue

            avg_cost_per_share = None
            open_cost_basis = 0.0
            if buy_qty > 0:
                avg_cost_per_share = total_buy_cost / buy_qty
                open_cost_basis = avg_cost_per_share * net_qty

            holdings.append(
                {
                    "SecurityID": sid,
                    "Ticker": ticker,
                    "SecType": sec_type,
                    "BuyQty": buy_qty,
                    "SellQty": sell_qty,
                    "NetQty": net_qty,
                    "TotalBuyCost": total_buy_cost,
                    "AvgCost": avg_cost_per_share,
                    "OpenCostBasis": open_cost_basis,
                }
            )

        if not holdings:
            print("\nNo open positions (net quantity) found for this portfolio.")
            return

        # 2) Pull latest prices and compute values / P&L based on OPEN cost basis
        total_invested = 0.0      # sum of open cost basis
        total_market_value = 0.0

        for h in holdings:
            sid = h["SecurityID"]

            cursor.execute(
                """
                SELECT ClosePrice, SnapshotTime
                FROM price_snapshot
                WHERE SecurityID = %s
                ORDER BY SnapshotTime DESC
                LIMIT 1
                """,
                (sid,)
            )
            price_row = cursor.fetchone()
            if price_row:
                last_price, snap_time = price_row
                last_price = float(last_price)
            else:
                last_price, snap_time = None, None

            net_qty = float(h["NetQty"])
            open_cost_basis = float(h["OpenCostBasis"])

            if last_price is not None:
                market_value = net_qty * last_price
            else:
                market_value = 0.0

            unrealized_pl = market_value - open_cost_basis
            unrealized_pl_pct = (unrealized_pl / open_cost_basis * 100.0) if open_cost_basis > 0 else 0.0

            total_invested += open_cost_basis
            total_market_value += market_value

            h["LastPrice"] = last_price
            h["SnapshotTime"] = snap_time
            h["MarketValue"] = market_value
            h["UnrealizedPL"] = unrealized_pl
            h["UnrealizedPLPct"] = unrealized_pl_pct

        total_unrealized_pl = total_market_value - total_invested
        total_unrealized_pl_pct = (total_unrealized_pl / total_invested * 100.0) if total_invested > 0 else 0.0

        pname = _load_portfolio_name(portfolio_id)
        print(f"\n=== Portfolio Snapshot for {pname} (ID={portfolio_id}) ===")
        print(f"Total Invested        : {total_invested:,.2f}")
        print(f"Total Market Value    : {total_market_value:,.2f}")
        print(f"Unrealized P/L        : {total_unrealized_pl:,.2f} ({total_unrealized_pl_pct:+.2f}%)")
        print("-" * 70)
        print(f"{'Ticker':<8} {'Type':<8} {'Shares':>8} {'AvgCost':>10} {'Last':>10} {'MktValue':>12} {'Unrlzd P/L':>12}")
        print("-" * 70)

        holdings_sorted = sorted(holdings, key=lambda h: h["MarketValue"], reverse=True)

        for h in holdings_sorted:
            ticker = h["Ticker"]
            sec_type = h["SecType"]
            net_qty = h["NetQty"]
            avg_cost = h["AvgCost"]
            last_price = h["LastPrice"]
            mkt_val = h["MarketValue"]
            pl = h["UnrealizedPL"]

            avg_cost_str = f"{avg_cost:.2f}" if avg_cost is not None else "N/A"
            last_price_str = f"{last_price:.2f}" if last_price is not None else "N/A"
            mkt_val_str = f"{mkt_val:,.2f}"
            pl_str = f"{pl:,.2f}"

            print(f"{ticker:<8} {sec_type:<8} {net_qty:>8.2f} {avg_cost_str:>10} {last_price_str:>10} {mkt_val_str:>12} {pl_str:>12}")

        print("-" * 70)
        print("✅ End of snapshot.")

    except Exception as e:
        print(f"[ERROR] Failed to compute portfolio snapshot value: {e}")
    finally:
        cursor.close()
        conn.close()

