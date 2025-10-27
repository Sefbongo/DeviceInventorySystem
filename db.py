import sqlite3
from pathlib import Path
import sys
import os

# Determine base directory depending on whether running as .exe or .py
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)  # PyInstaller temp folder
    # Use the folder where the .exe resides for DB files
    EXE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
    EXE_DIR = BASE_DIR

DB_FILE = str(EXE_DIR / "DeviceInventory.db")
ACCOUNTS_DB = str(EXE_DIR / "accounts.db")

def get_inventory_conn():
    return sqlite3.connect(DB_FILE)

def get_accounts_conn():
    return sqlite3.connect(ACCOUNTS_DB)

def init_inventory_db():
    conn = get_inventory_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_class TEXT,
        asset_id TEXT,
        asset_name TEXT,
        manufactured_date TEXT,
        date_acquired TEXT,
        business_unit TEXT,
        department TEXT,
        branch TEXT,
        brand TEXT,
        description TEXT,
        serial_number TEXT,
        custodian TEXT,
        device_status TEXT,
        cancelled INTEGER DEFAULT 0
    )
    """)
    # Create supporting tables
    cur.execute("CREATE TABLE IF NOT EXISTS asset_classes (name TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS description (name TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS business_units (name TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS departments (name TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS branches (name TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS device_status (name TEXT UNIQUE)")
    conn.commit()
    conn.close()

def init_user_db():
    conn = get_accounts_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) FROM accounts")
    if cur.fetchone()[0] == 0:
        # Add default accounts only if DB is empty
        cur.execute("INSERT INTO accounts (username, password, role) VALUES (?, ?, ?)",
                    ("ADMIN", "ADMIN", "Administrator"))
        cur.execute("INSERT INTO accounts (username, password, role) VALUES (?, ?, ?)",
                    ("USER", "123USER", "User"))
    conn.commit()
    conn.close()

def fetch_values(table):
    conn = get_inventory_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT name FROM {table} ORDER BY name")
        vals = [row[0] for row in cur.fetchall()]
    except sqlite3.OperationalError:
        vals = []
    conn.close()
    return vals

def get_branches():
    conn = get_inventory_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM branches ORDER BY name")
        rows = [r[0] for r in cur.fetchall() if r[0]]
        if rows:
            conn.close()
            return rows
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("SELECT DISTINCT branch FROM inventory WHERE branch IS NOT NULL AND branch<>'' ORDER BY branch")
        rows = [r[0] for r in cur.fetchall() if r[0]]
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return rows
