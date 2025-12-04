#Low-level DB connection helper
import json
import mysql.connector
from mysql.connector import Error

def load_config(path: str = "db_config.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_connection():
    cfg = load_config()
    try:
        conn = mysql.connector.connect(
            host=cfg.get("host", "localhost"),
            port=cfg.get("port", 3306),
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
        )
        return conn
    except Error as e:
        print(f"[DB ERROR] Failed to connect: {e}")
        return None
