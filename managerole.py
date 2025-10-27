import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3

def build_manage_role_tab(root, notebook, cursor, conn, refresh_all_comboboxes):
    tab_roles = ttk.Frame(notebook)
    notebook.add(tab_roles, text="🛠 EDIT CATEGORIES")

    role_frame = ttk.LabelFrame(tab_roles, text="EDIT CATEGORIES", padding=15)
    role_frame.pack(fill="x", padx=20, pady=15)

    role_tables = {
        "TOOL OF TRADE": "asset_classes",
        "BUSINESS UNIT": "business_units",
        "DEPARTMENT": "departments",
        "BRANCH": "branches",
        "ASSET STATUS": "device_status",
        "ASSET DESCRIPTION": "description"
    }


    tk.Label(role_frame, text="SELECT CATEGORY TYPE:", bg="#E0DDD9").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    role_type_var = tk.StringVar(value="TOOL OF TRADE")
    role_type_cb = ttk.Combobox(role_frame, textvariable=role_type_var, state="readonly",
                                values=list(role_tables.keys()), width=20)
    role_type_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    tk.Label(role_frame, text="SELECT CATEGORY ITEM:", bg="#E0DDD9").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    role_item_var = tk.StringVar()
    role_item_cb = ttk.Combobox(role_frame, textvariable=role_item_var, state="readonly", width=30)
    role_item_cb.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def refresh_role_items(event=None):
        table = role_tables[role_type_var.get()]
        conn.commit() 
        cur = conn.cursor()
        cur.execute(f"SELECT name FROM {table} ORDER BY name")
        items = [row[0] for row in cur.fetchall()]
        role_item_cb['values'] = items
        if items:
            role_item_cb.current(0)
        else:
            role_item_cb.set("")

    role_type_cb.bind("<<ComboboxSelected>>", refresh_role_items)
    refresh_role_items()

    
    def add_role():
        table = role_tables[role_type_var.get()]
        new_item = simpledialog.askstring("Add", f"Enter new {role_type_var.get()}:")
        if new_item:
            try:
                cursor.execute(f"INSERT INTO {table} (name) VALUES (?)", (new_item.strip(),))
                conn.commit()
                
                refresh_role_items()
                messagebox.showinfo("Added", f"{role_type_var.get()} '{new_item}' added!")
            except sqlite3.IntegrityError:
                messagebox.showwarning("Exists", f"{new_item} already exists.")

    def edit_role():
        table = role_tables[role_type_var.get()]
        old = role_item_var.get()
        if not old:
            messagebox.showwarning("Select", f"Please select a {role_type_var.get()} to edit.")
            return
        new = simpledialog.askstring("Edit", f"Rename '{old}' to:", initialvalue=old)
        if new and new.strip():
            try:
                cursor.execute(f"UPDATE {table} SET name=? WHERE name=?", (new.strip(), old))
                conn.commit()
                refresh_role_items()
                messagebox.showinfo("Updated", f"{old} updated to '{new}'")
            except sqlite3.IntegrityError:
                messagebox.showwarning("Exists", f"{new} already exists.")

    def delete_role():
        table = role_tables[role_type_var.get()]
        selected = role_item_var.get()
        if not selected:
            messagebox.showwarning("Select", f"Please select a {role_type_var.get()} to delete.")
            return
        if messagebox.askyesno("Delete", f"Are you sure you want to delete '{selected}'?"):
            cursor.execute(f"DELETE FROM {table} WHERE name=?", (selected,))
            conn.commit()
            
            refresh_role_items()
            messagebox.showinfo("Deleted", f"{selected} deleted!")

   
    tk.Button(role_frame, text="➕ Add", command=add_role, bg="#3498db", fg="white", width=12).grid(row=2, column=0, padx=5, pady=5)
    tk.Button(role_frame, text="✏️ Edit", command=edit_role, bg="#f39c12", fg="white", width=12).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(role_frame, text="🗑 Delete", command=delete_role, bg="#e74c3c", fg="white", width=12).grid(row=2, column=2, padx=5, pady=5)
