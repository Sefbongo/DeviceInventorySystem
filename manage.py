import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from openpyxl import Workbook
from db import get_inventory_conn

def build_manage_tab(root, notebook, current_user_role):
    conn = get_inventory_conn()
    cursor = conn.cursor()

    tab = ttk.Frame(notebook)
    notebook.add(tab, text="📂 Manage Devices")

   
    search_frame = ttk.LabelFrame(tab, text="Search", padding=10)
    search_frame.pack(fill="x", padx=20, pady=10)
    tk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5)
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=50)
    search_entry.grid(row=0, column=1, padx=5)

    tk.Button(search_frame, text="Search", command=lambda: search_records(), width=12).grid(row=0, column=2, padx=5)
    search_entry.bind("<Return>", lambda e: search_records())

   
    FIELDS = [
        "id", "asset_class", "asset_id", "asset_name", "manufactured_date", "date_acquired",
        "business_unit", "department", "branch", "brand", "description", "serial_number",
        "custodian", "device_status", "cancelled"
    ]
    HEADERS = [
        "ID", "TOOL OF TRADE", "ASSET ID", "ASSET NAME", "MANUFACTURED DATE", "DATE ACQUIRED",
        "BUSINESS UNIT", "DEPARTMENT", "BRANCH", "BRAND", "ASSET DESCRIPTION",
        "SERIAL NUMBER", "CUSTODIAN", "ASSET STATUS", "CANCELLED"
    ]

   
    display_frame = ttk.LabelFrame(tab, text="Inventory Records", padding=10)
    display_frame.pack(fill="both", expand=True, padx=20, pady=10)
    tree = ttk.Treeview(display_frame, columns=HEADERS, show="headings", height=18)
    for col in HEADERS:
        tree.heading(col, text=col)
        tree.column(col, width=120, stretch=True)
    tree.pack(fill="both", expand=True, side="left")
    scroll_y = ttk.Scrollbar(display_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scroll_y.set)
    scroll_y.pack(side="right", fill="y")

   
    cancelled_tree = None
    if current_user_role == "Administrator":
        tab_cancelled = ttk.Frame(notebook)
        notebook.add(tab_cancelled, text="🗑 Cancelled Records")
        cancelled_frame = ttk.LabelFrame(tab_cancelled, text="Cancelled Records", padding=10)
        cancelled_frame.pack(fill="both", expand=True, padx=20, pady=10)
        cancelled_tree = ttk.Treeview(cancelled_frame, columns=HEADERS, show="headings", height=18)
        for col in HEADERS:
            cancelled_tree.heading(col, text=col)
            cancelled_tree.column(col, width=120, stretch=True)
        cancelled_tree.pack(fill="both", expand=True, side="left")
        cancelled_scroll_y = ttk.Scrollbar(cancelled_frame, orient="vertical", command=cancelled_tree.yview)
        cancelled_tree.configure(yscroll=cancelled_scroll_y.set)
        cancelled_scroll_y.pack(side="right", fill="y")

        def restore_record():
            selected = cancelled_tree.focus()
            if not selected:
                messagebox.showwarning("Select Record", "Please select a record to restore.")
                return
            record_id = cancelled_tree.item(selected, "values")[0]
            if messagebox.askyesno("Restore", "Do you want to restore this record?"):
                cursor.execute("UPDATE inventory SET cancelled=0 WHERE id=?", (record_id,))
                conn.commit()
                refresh_manage()
                load_cancelled_records()
                messagebox.showinfo("Restored", "Record has been restored.")

        tk.Button(tab_cancelled, text="♻️ Restore Selected", command=restore_record,
                  bg="#27ae60", fg="white", width=18, height=2).pack(pady=10)

 
    filter_applied = False

    def load_all_records():
        nonlocal filter_applied
        cursor.execute(f"SELECT {', '.join(FIELDS)} FROM inventory WHERE cancelled=0")
        records = cursor.fetchall()
        tree.delete(*tree.get_children())
        for r in records:
            tree.insert("", tk.END, values=r)
        filter_applied = False

    def load_cancelled_records():
        if cancelled_tree is None:
            return
        cursor.execute(f"SELECT {', '.join(FIELDS)} FROM inventory WHERE cancelled=1")
        records = cursor.fetchall()
        cancelled_tree.delete(*cancelled_tree.get_children())
        for r in records:
            cancelled_tree.insert("", tk.END, values=r)

  
    def search_records(event=None):
        nonlocal filter_applied
        term = search_var.get().strip()
        if not term:
            load_all_records()
            return

        search_columns = [
            "asset_class", "asset_id", "asset_name", "manufactured_date", "business_unit",
            "department", "branch", "brand", "description", "serial_number",
            "custodian", "device_status"
        ]
        conditions = " OR ".join([f"{col} LIKE ? COLLATE NOCASE" for col in search_columns])
        params = [f"%{term}%"] * len(search_columns)

        cursor.execute(f"SELECT {', '.join(FIELDS)} FROM inventory WHERE cancelled=0 AND ({conditions})", params)
        records = cursor.fetchall()
        tree.delete(*tree.get_children())
        for r in records:
            tree.insert("", tk.END, values=r)
        filter_applied = True

   
    def export_filtered():
        records = [tree.item(child)["values"] for child in tree.get_children()]
        if not records:
            messagebox.showwarning("No Data", "No records to export.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")])
        if not file:
            return
        wb = Workbook()
        ws = wb.active
        ws.append(HEADERS)
        for r in records:
            ws.append(r)
        wb.save(file)
        messagebox.showinfo("Exported", f"Data exported to {file}")

 
    def cancel_record():
        if current_user_role != "Administrator":
            messagebox.showerror("Permission Denied", "Only administrators can cancel records!")
            return
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to cancel.")
            return
        record_id = tree.item(selected, "values")[0]
        if messagebox.askyesno("Cancel", "Are you sure you want to cancel this record?"):
            cursor.execute("UPDATE inventory SET cancelled=1 WHERE id=?", (record_id,))
            conn.commit()
            refresh_manage()
            load_cancelled_records()
            messagebox.showinfo("Cancelled", "Record has been cancelled.")

   
    def edit_record():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to edit.")
            return
        record = tree.item(selected, "values")
        record_id = record[0]

        edit_win = tk.Toplevel(root)
        edit_win.title(f"Edit Record ID {record_id}")
        edit_entries = {}
        for i, field in enumerate(HEADERS[1:-1]):  
            tk.Label(edit_win, text=field).grid(row=i, column=0, padx=5, pady=3, sticky="w")
            entry = tk.Entry(edit_win, width=35)
            entry.insert(0, record[i+1])
            entry.grid(row=i, column=1, padx=5, pady=3)
            edit_entries[field] = entry

        def save_edit():
            values = [e.get() for e in edit_entries.values()]
            cursor.execute(f"""
                UPDATE inventory SET
                asset_class=?, asset_id=?, asset_name=?, manufactured_date=?, date_acquired=?,
                business_unit=?, department=?, branch=?, brand=?, description=?,
                serial_number=?, custodian=?, device_status=?
                WHERE id=?
            """, values + [record_id])
            conn.commit()
            messagebox.showinfo("Updated", "Record updated successfully!")
            edit_win.destroy()
            refresh_manage()

        tk.Button(edit_win, text="💾 Save Changes", command=save_edit,
                  bg="#28b463", fg="white").grid(row=len(edit_entries), column=0, columnspan=2, pady=10)

   
    btn_manage_frame = tk.Frame(tab, bg="#E0DDD9")
    btn_manage_frame.pack(pady=10)
    tk.Button(btn_manage_frame, text="✏️ Edit", command=edit_record, bg="#3498db", fg="white", width=12, height=2).grid(row=0,column=0,padx=5)
    tk.Button(btn_manage_frame, text="🗑 Cancel", command=cancel_record, bg="#e74c3c", fg="white", width=12, height=2).grid(row=0,column=1,padx=5)
    tk.Button(btn_manage_frame, text="📤 Export Filtered", command=export_filtered, bg="#f39c12", fg="white", width=15, height=2).grid(row=0,column=2,padx=5)

    
    def refresh_manage():
        load_all_records()

    # --- Initial load ---
    refresh_manage()
    load_cancelled_records()

    return tab, refresh_manage
