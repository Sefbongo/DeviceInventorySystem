import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import platform, subprocess, sys, getpass

from db import init_inventory_db, init_user_db, get_inventory_conn, get_accounts_conn
from tabs.add_device import build_add_tab
from tabs.manage import build_manage_tab
from tabs.managerole import build_manage_role_tab
from tabs.manageuser import build_manageuser_tab
from tabs.reports import build_reports_tab


init_inventory_db()
init_user_db()

def login_prompt():
    login_window = tk.Tk()
    login_window.title("Login")
    login_window.resizable(False, False)


    window_width, window_height = 350, 220
    screen_width = login_window.winfo_screenwidth()
    screen_height = login_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    login_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    tk.Label(login_window, text="Username:").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    role_var = tk.StringVar(value="")

    def check_login():
        user = username_entry.get().strip()
        pwd = password_entry.get().strip()
        conn = get_accounts_conn()
        cur = conn.cursor()
        cur.execute("SELECT role FROM accounts WHERE username=? AND password=?", (user, pwd))
        row = cur.fetchone()
        conn.close()
        if row:
            role_var.set(row[0])
            login_window.destroy()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password!")

    tk.Button(login_window, text="Login", command=check_login, width=12, bg="#3498db", fg="white").pack(pady=15)

    def on_close():
        sys.exit()
    login_window.protocol("WM_DELETE_WINDOW", on_close)
    login_window.mainloop()
    return role_var.get()


current_user_role = login_prompt()
if not current_user_role:
    sys.exit()



def get_platform_info():
    device_name = platform.node()
    serial_number = brand = manufactured_date = "Unknown"

    if platform.system() == "Windows":
 
        try:
            serial_number = (
                subprocess.check_output("wmic bios get serialnumber", shell=True)
                .decode(errors="ignore")
                .split("\n")[1].strip()
            ) or "Unknown"
        except Exception:
            serial_number = "Unknown"

        if serial_number == "Unknown":
            try:
                serial_number = (
                    subprocess.check_output(
                        'powershell -Command "Get-WmiObject win32_bios | Select-Object -ExpandProperty SerialNumber"',
                        shell=True,
                    ).decode(errors="ignore").strip()
                ) or "Unknown"
            except Exception:
                pass


        try:
            brand = (
                subprocess.check_output("wmic computersystem get manufacturer", shell=True)
                .decode(errors="ignore")
                .split("\n")[1].strip()
            ) or "Unknown"
        except Exception:
            brand = "Unknown"

        if brand == "Unknown":
            try:
                brand = (
                    subprocess.check_output(
                        'powershell -Command "Get-WmiObject win32_computersystem | Select-Object -ExpandProperty Manufacturer"',
                        shell=True,
                    ).decode(errors="ignore").strip()
                ) or "Unknown"
            except Exception:
                pass

        try:
            raw_date = (
                subprocess.check_output("wmic bios get ReleaseDate", shell=True)
                .decode(errors="ignore")
                .split("\n")[1].strip()
            )
            manufactured_date = (
                f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if raw_date else "Unknown"
            )
        except Exception:
            manufactured_date = "Unknown"

        if manufactured_date == "Unknown":
            try:
                raw_date = (
                    subprocess.check_output(
                        'powershell -Command "Get-WmiObject win32_bios | Select-Object -ExpandProperty ReleaseDate"',
                        shell=True,
                    ).decode(errors="ignore").strip()
                )
                manufactured_date = (
                    f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if raw_date else "Unknown"
                )
            except Exception:
                pass

    return (brand, device_name, serial_number, manufactured_date)


platform_info = get_platform_info()

root = tk.Tk()
root.title("📋 Asset Inventory System")


try:
    root.state("zoomed")  
except Exception:
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}")

root.configure(bg="#f4f6f7")

style = ttk.Style()
try:
    style.theme_use("clam")
except Exception:
    pass
style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#2e86c1", foreground="white")
style.configure("Treeview", font=("Segoe UI", 9), rowheight=25)
style.map("Treeview", background=[("selected", "#5dade2")])

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=15, pady=15)

conn = get_inventory_conn()
accounts_conn = get_accounts_conn()
cursor = conn.cursor()

refresh_manage_callback = build_manage_tab(root, notebook, current_user_role)
build_add_tab(root, notebook, platform_info, refresh_manage_callback=refresh_manage_callback)
build_reports_tab(root, notebook)

if current_user_role == "Administrator":
    build_manageuser_tab(root, notebook, current_user_role)
    build_manage_role_tab(root, notebook, cursor, conn, current_user_role)

root.mainloop()
