
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

def build_manageuser_tab(root, notebook, current_user_role):
    """
    Build the 'Manage Users' tab for Administrators only.
    """
    if current_user_role != "Administrator":
        messagebox.showerror("Access Denied", "Only Administrators can access User Management.")
        return None

    tab = ttk.Frame(notebook)
    notebook.add(tab, text="👤 MANAGE USER")

    HEADERS = ["ID", "USERNAME", "ROLE"]
    tree_frame = ttk.LabelFrame(tab, text="USER LIST", padding=10)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

    tree = ttk.Treeview(tree_frame, columns=HEADERS, show="headings", height=15)
    for col in HEADERS:
        tree.heading(col, text=col)
        tree.column(col, width=150, stretch=True)
    tree.pack(fill="both", expand=True, side="left")

    scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scroll_y.set)
    scroll_y.pack(side="right", fill="y")

    def get_accounts_conn():
        return sqlite3.connect("accounts.db")

    def load_users():
        conn = get_accounts_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role FROM accounts")
        records = cur.fetchall()
        tree.delete(*tree.get_children())
        for r in records:
            tree.insert("", tk.END, values=r)
        conn.close()

    def add_user():
        add_win = tk.Toplevel(root)
        add_win.title("Add New User")

        tk.Label(add_win, text="Username:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        username_entry = tk.Entry(add_win)
        username_entry.grid(row=0, column=1, padx=5, pady=3)

        tk.Label(add_win, text="Password:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        password_entry = tk.Entry(add_win, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=3)

        tk.Label(add_win, text="Role:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        role_combo = ttk.Combobox(add_win, values=["Administrator", "User"], state="readonly")
        role_combo.grid(row=2, column=1, padx=5, pady=3)
        role_combo.set("User")

        def save_user():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            role = role_combo.get()
            if not username or not password:
                messagebox.showwarning("Input Error", "Username and password cannot be empty.")
                return
            try:
                conn = get_accounts_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO accounts (username, password, role) VALUES (?, ?, ?)",
                            (username, password, role))
                conn.commit()
                conn.close()
                load_users()
                messagebox.showinfo("Success", f"User '{username}' added successfully.")
                add_win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")

        tk.Button(add_win, text="💾 Save", command=save_user, bg="#28b463", fg="white").grid(row=3, column=0, columnspan=2, pady=10)

    def edit_user():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Select User", "Please select a user to edit.")
            return
        record = tree.item(selected, "values")
        user_id, username, role = record

        edit_win = tk.Toplevel(root)
        edit_win.title(f"Edit User ID {user_id}")

        tk.Label(edit_win, text="Username:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        username_entry = tk.Entry(edit_win)
        username_entry.grid(row=0, column=1, padx=5, pady=3)
        username_entry.insert(0, username)

        tk.Label(edit_win, text="Password:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        password_entry = tk.Entry(edit_win, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=3)

        tk.Label(edit_win, text="Role:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        role_combo = ttk.Combobox(edit_win, values=["Administrator", "User"], state="readonly")
        role_combo.grid(row=2, column=1, padx=5, pady=3)
        role_combo.set(role)

        def save_edit():
            new_username = username_entry.get().strip()
            new_password = password_entry.get().strip()
            new_role = role_combo.get()
            if not new_username:
                messagebox.showwarning("Input Error", "Username cannot be empty.")
                return
            try:
                conn = get_accounts_conn()
                cur = conn.cursor()
                if new_password:
                    cur.execute("UPDATE accounts SET username=?, password=?, role=? WHERE id=?",
                                (new_username, new_password, new_role, user_id))
                else:
                    cur.execute("UPDATE accounts SET username=?, role=? WHERE id=?",
                                (new_username, new_role, user_id))
                conn.commit()
                conn.close()
                load_users()
                messagebox.showinfo("Updated", "User updated successfully.")
                edit_win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")

        tk.Button(edit_win, text="💾 Save Changes", command=save_edit, bg="#28b463", fg="white").grid(row=3, column=0, columnspan=2, pady=10)

    def delete_user():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Select User", "Please select a user to delete.")
            return
        record = tree.item(selected, "values")
        user_id, username, _ = record
        if messagebox.askyesno("Delete User", f"Are you sure you want to delete '{username}'?"):
            conn = get_accounts_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM accounts WHERE id=?", (user_id,))
            conn.commit()
            conn.close()
            load_users()
            messagebox.showinfo("Deleted", f"User '{username}' deleted successfully.")


    btn_frame = tk.Frame(tab, bg="#E0DDD9")
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="➕ Add User", command=add_user, bg="#3498db", fg="white", width=12, height=2).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="✏️ Edit User", command=edit_user, bg="#f1c40f", fg="white", width=12, height=2).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="🗑 Delete User", command=delete_user, bg="#e74c3c", fg="white", width=12, height=2).grid(row=0, column=2, padx=5)


    load_users()
    return tab
