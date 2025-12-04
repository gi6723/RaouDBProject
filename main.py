from db import get_connection
from portfolio_functions import create_portfolio, move_portfolio_to_account
from security_functions import add_security_tag
from trade_functions import record_trade, record_dividend, trade_history_by_security
from price_functions import import_price_snapshot_manual
from report_functions import holdings_report, portfolio_snapshot_value

#Global Session Variables
current_user_id = None
current_user_email = None


# ---------- AUTH HELPERS ----------

def sign_up():
    global current_user_id, current_user_email

    print("\n=== Sign Up ===")
    email = input("Primary email: ").strip()
    if not email:
        print("Email is required.")
        return

    password = input("Password (plain text for demo): ").strip()
    if not password:
        print("Password is required.")
        return

    fname = input("First name: ").strip()
    if not fname:
        print("First name required.")
        return

    lname = input("Last name: ").strip()
    if not lname:
        print("Last name is required.")
        return

    mname = input("Middle name (optional): ").strip() or None

    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute(
            "SELECT UserID FROM app_user WHERE PrimaryEmail = %s",
            (email,)
        )
        existing = cursor.fetchone()
        if existing:
            print("An account with that email already exists. Please log in instead.")
            return

        insert_sql = """
            INSERT INTO app_user (PrimaryEmail, PasswordHash, Fname, Mname, Lname)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (email, password, fname, mname, lname))
        conn.commit()

        current_user_id = cursor.lastrowid
        current_user_email = email
        print(f"\n✅ Account created. Logged in as {email} (UserID={current_user_id}).")

    except Exception as e:
        print(f"[ERROR] Failed to create user: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def log_in():
    global current_user_id, current_user_email

    print("\n=== Log In ===")
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    conn = get_connection()
    if conn is None:
        print("[ERROR] Could not connect to database.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT UserID, PasswordHash
            FROM app_user
            WHERE PrimaryEmail = %s
            """,
            (email,)
        )
        row = cursor.fetchone()
        if not row:
            print("No user found with that email. Try again or sign up.")
            return

        user_id, stored_pw = row
        if password != stored_pw:
            print("Incorrect password.")
            return

        current_user_id = user_id
        current_user_email = email
        print(f"\n✅ Logged in as {email} (UserID={current_user_id}).")

    except Exception as e:
        print(f"[ERROR] Failed to log in: {e}")
    finally:
        cursor.close()
        conn.close()


def require_login():
    global current_user_id

    while current_user_id is None:
        print("\n===================================")
        print("  Portfolio Manager - Authentication")
        print("===================================")
        print("1. Log in")
        print("2. Sign up (create new account)")
        print("0. Exit")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            log_in()
        elif choice == "2":
            sign_up()
        elif choice == "0":
            return False
        else:
            print("Invalid choice. Please try again.")

    return True


# ---------- MAIN APP MENU ----------

def app_menu():
    from time import sleep
    global current_user_id, current_user_email

    if not require_login():
        print("Goodbye!")
        return

    while True:
        print("\n===================================")
        print(" Welcome to your Portfolio Manager ")
        print("===================================")
        print(f"Logged in as: {current_user_email} (UserID={current_user_id})")
        print("-----------------------------------")
        print("1. Create portfolio")
        print("2. Record trade (BUY/SELL)")
        print("3. Record dividend")
        print("4. Import price snapshot")
        print("5. Show portfolio snapshot value")
        print("6. View holdings report")
        print("7. View trade history by security")
        print("8. Move portfolio to another account")
        print("9. Add security tag to a security")
        print("L. Log in as a different user")
        print("0. Exit")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            create_portfolio(current_user_id)
        elif choice == "2":
            record_trade(current_user_id)
        elif choice == "3":
            record_dividend(current_user_id)
        elif choice == "4":
            import_price_snapshot_manual()
        elif choice == "5":
            portfolio_snapshot_value(current_user_id)
        elif choice == "6":
            holdings_report(current_user_id)
        elif choice == "7":
            trade_history_by_security(current_user_id)
        elif choice == "8":
            move_portfolio_to_account(current_user_id)
        elif choice == "9":
            add_security_tag(current_user_id)
        elif choice.lower() == "l":
            current_user_id = None
            current_user_email = None
            if not require_login():
                print("Goodbye!")
                break
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

        sleep(0.3)


if __name__ == "__main__":
    app_menu()
