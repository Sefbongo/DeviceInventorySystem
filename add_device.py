import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import getpass
import pandas as pd

from widgets import AutocompleteCombobox, add_row
from db import get_inventory_conn, fetch_values, get_branches

def build_add_tab(root, notebook, platform_info, refresh_manage_callback=None):
    conn = get_inventory_conn()
    cursor = conn.cursor()

    tab = ttk.Frame(notebook)
    notebook.add(tab, text="➕ ADD DEVICE")

    form_frame = ttk.LabelFrame(tab, text="ASSET DETAIL", padding=15)
    form_frame.pack(fill="x", padx=20, pady=10)

   
    cb_asset = ttk.Combobox(form_frame, values=[], state="readonly", width=30)
    cb_unit  = ttk.Combobox(form_frame, values=[], state="readonly", width=30)
    cb_dept  = ttk.Combobox(form_frame, values=[], state="readonly", width=30)
    cb_branch = AutocompleteCombobox(form_frame, width=30)
    cb_status = ttk.Combobox(form_frame, values=[], state="readonly", width=30)
    cb_desc   = ttk.Combobox(form_frame, values=[], state="readonly", width=70)

    brand, device_name, serial_number, manufactured_date = platform_info
    brand_entry = tk.Entry(form_frame, width=34)
    brand_entry.insert(0, brand)
    brand_entry.config(state="readonly")
    device_entry = tk.Entry(form_frame, width=34)
    device_entry.insert(0, device_name)
    device_entry.config(state="readonly")
    serial_entry = tk.Entry(form_frame, width=34)
    serial_entry.insert(0, serial_number)
    serial_entry.config(state="readonly")
    mdate_entry = tk.Entry(form_frame, width=34)
    mdate_entry.insert(0, manufactured_date)
    mdate_entry.config(state="readonly")
    date_acquired_entry = DateEntry(form_frame, width=32, background='darkblue',
                                    foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    date_acquired_entry.set_date(datetime.now())
    custodian_entry = tk.Entry(form_frame, width=34)
    custodian_entry.insert(0, getpass.getuser())

   
    add_row(form_frame, 0, 0, "TOOL OF TRADE", cb_asset)
    add_row(form_frame, 0, 2, "BUSINESS UNIT", cb_unit)
    add_row(form_frame, 1, 0, "DEPARTMENT", cb_dept)
    add_row(form_frame, 1, 2, "BRANCH", cb_branch)
    add_row(form_frame, 2, 0, "ASSET STATUS", cb_status)
    add_row(form_frame, 2, 2, "BRAND", brand_entry)
    add_row(form_frame, 3, 0, "DEVICE NAME", device_entry)
    add_row(form_frame, 3, 2, "SERIAL NUMBER", serial_entry)
    add_row(form_frame, 4, 0, "MANUFACTURE DATE", mdate_entry)
    add_row(form_frame, 4, 2, "DATE RECEIVED", date_acquired_entry)
    add_row(form_frame, 5, 0, "ASSET DESCRIPTION", cb_desc)
    add_row(form_frame, 5, 2, "CUSTODIAN", custodian_entry)

   
    def refresh_all_comboboxes():
        try:
            vals = fetch_values("asset_classes")
            cb_asset['values'] = vals
            if vals and not cb_asset.get(): cb_asset.current(0)
        except: pass
        try:
            vals = fetch_values("business_units")
            cb_unit['values'] = vals
            if vals and not cb_unit.get(): cb_unit.current(0)
        except: pass
        try:
            vals = fetch_values("departments")
            cb_dept['values'] = vals
            if vals and not cb_dept.get(): cb_dept.current(0)
        except: pass
        try:
            vals = get_branches()
            cb_branch.set_completion_list(vals)
            if vals and not cb_branch.get(): cb_branch.set("")
        except: pass
        try:
            vals = fetch_values("description")
            cb_desc['values'] = vals
            if vals and not cb_desc.get(): cb_desc.current(0)
        except: pass
        try:
            vals = fetch_values("device_status")
            cb_status['values'] = vals
            if vals and not cb_status.get(): cb_status.current(0)
        except: pass

    
    def save_to_db():
        required_fields = {
            "Tool of Trade": cb_asset.get().strip(),
            "Device Name": device_entry.get().strip(),
            "Date Acquired": date_acquired_entry.get_date().strftime("%Y-%m-%d"),
            "Business Unit": cb_unit.get().strip(),
            "Department": cb_dept.get().strip(),
            "Branch": cb_branch.get().strip(),
            "Brand": brand_entry.get().strip(),
            "Asset Description": cb_desc.get().strip(),
            "Serial Number": serial_entry.get().strip(),
            "Custodian": custodian_entry.get().strip(),
            "Asset Status": cb_status.get().strip()
        }

        empty_fields = [name for name, val in required_fields.items() if not val]
        if empty_fields:
            messagebox.showwarning("Missing Data", f"Please fill the following fields:\n{', '.join(empty_fields)}")
            return

        serial = serial_entry.get().strip()
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE serial_number=? AND cancelled=0", (serial,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Duplicate Entry", "This serial number already exists in the database!")
            return

        cursor.execute("SELECT COUNT(*) FROM inventory")
        asset_id = f"ASSET_{cursor.fetchone()[0]+1:05d}"

        cursor.execute("""
            INSERT INTO inventory (
                asset_class, asset_id, asset_name, manufactured_date, date_acquired,
                business_unit, department, branch, brand, description,
                serial_number, custodian, device_status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            cb_asset.get().strip(), asset_id, device_entry.get().strip(), mdate_entry.get().strip(),
            date_acquired_entry.get_date().strftime("%Y-%m-%d"), cb_unit.get().strip(),
            cb_dept.get().strip(), cb_branch.get().strip(), brand_entry.get().strip(),
            cb_desc.get().strip(), serial_entry.get().strip(), custodian_entry.get().strip(),
            cb_status.get().strip()
        ))
        conn.commit()
        messagebox.showinfo("Saved", "Asset details saved successfully!")
        refresh_all_comboboxes()
        

    def clear_form():
        date_acquired_entry.set_date(datetime.now())
        for cb in (cb_asset, cb_unit, cb_dept, cb_branch, cb_status, cb_desc):
            try: cb.set("")
            except: pass

    
    def add_manual_entry():
        win = tk.Toplevel(root)
        win.title("➕ Manual Entry")
        entry_widgets = {}

        cursor.execute("SELECT COUNT(*) FROM inventory")
        next_asset_id = f"ASSET_{cursor.fetchone()[0]+1:05d}"

        manual_fields = [
            "TOOL OF TRADE", "ASSET ID", "DEVICE NAME", "MANUFACTURED DATE",
            "DATE ACQUIRED", "BUSINESS UNIT", "DEPARTMENT", "BRANCH",
            "BRAND", "ASSET DESCRIPTION", "SERIAL NUMBER", "CUSTODIAN", "ASSET STATUS"
        ]

        combobox_map = {
            "TOOL OF TRADE": cb_asset['values'],
            "BUSINESS UNIT": cb_unit['values'],
            "DEPARTMENT": cb_dept['values'],
            "BRANCH": cb_branch._completion_list,
            "ASSET STATUS": cb_status['values'],
            "ASSET DESCRIPTION": cb_desc['values']
        }

        for i, field in enumerate(manual_fields):
            tk.Label(win, text=field).grid(row=i, column=0, padx=5, pady=3, sticky="w")
            if field in combobox_map:
                cb = ttk.Combobox(win, values=combobox_map[field], state="readonly", width=32)
                cb.set("")
                cb.grid(row=i, column=1, padx=5, pady=3)
                entry_widgets[field] = cb
            elif field in ["DATE ACQUIRED", "MANUFACTURED DATE"]:
                de = DateEntry(win, width=32, background='darkblue', foreground='white',
                               borderwidth=2, date_pattern='yyyy-mm-dd')
                de.set_date(datetime.now())
                de.grid(row=i, column=1, padx=5, pady=3)
                entry_widgets[field] = de
            elif field == "ASSET ID":
                entry = tk.Entry(win, width=35)
                entry.insert(0, next_asset_id)
                entry.config(state="readonly")
                entry.grid(row=i, column=1, padx=5, pady=3)
                entry_widgets[field] = entry
            else:
                entry = tk.Entry(win, width=35)
                entry.grid(row=i, column=1, padx=5, pady=3)
                if field == "CUSTODIAN": entry.insert(0, getpass.getuser())
                elif field == "BRAND": entry.insert(0, platform_info[0])
                entry_widgets[field] = entry

        def save_manual():
            values = []
            empty_fields = []
            for field in manual_fields:
                widget = entry_widgets[field]
                val = widget.get_date().strftime("%Y-%m-%d") if isinstance(widget, DateEntry) else widget.get().strip()
                if not val: empty_fields.append(field)
                values.append(val)
            if empty_fields:
                messagebox.showwarning("Missing Data", f"Please fill the following fields:\n{', '.join(empty_fields)}")
                return

            serial_number = entry_widgets["SERIAL NUMBER"].get().strip()
            cursor.execute("SELECT COUNT(*) FROM inventory WHERE serial_number=? AND cancelled=0", (serial_number,))
            if cursor.fetchone()[0] > 0:
                messagebox.showwarning("Duplicate Entry", "This serial number already exists!")
                return

            cursor.execute("""
                INSERT INTO inventory (
                    asset_class, asset_id, asset_name, manufactured_date, date_acquired,
                    business_unit, department, branch, brand, description,
                    serial_number, custodian, device_status
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, values)
            conn.commit()
            messagebox.showinfo("Saved", "Manual entry added successfully!")
            win.destroy()
            refresh_all_comboboxes()
           
                

        tk.Button(win, text="💾 Save Entry", command=save_manual, bg="#28b463", fg="white")\
            .grid(row=len(manual_fields), column=0, columnspan=2, pady=10)

    # --- Import file ---
    def import_file():
        file = filedialog.askopenfilename(filetypes=[("Excel files","*.xlsx;*.xls"), ("CSV files","*.csv")])
        if not file:
            return

        try:
            df = pd.read_csv(file) if file.lower().endswith(".csv") else pd.read_excel(file)
            imported_count = 0
            skipped_count = 0

            for _, row in df.iterrows():
                serial_number = row.get("SERIAL NUMBER", "").strip()
                if not serial_number:
                    skipped_count += 1
                    continue

                # Check for duplicate
                cursor.execute("SELECT COUNT(*) FROM inventory WHERE serial_number=? AND cancelled=0", (serial_number,))
                if cursor.fetchone()[0] > 0:
                    skipped_count += 1
                    continue

                # Auto-generate ASSET ID if missing
                cursor.execute("SELECT COUNT(*) FROM inventory")
                asset_id = row.get("ASSET ID") or f"ASSET_{cursor.fetchone()[0]+1:05d}"

                cursor.execute("""
                    INSERT INTO inventory (
                        asset_class, asset_id, asset_name, manufactured_date, date_acquired,
                        business_unit, department, branch, brand, description,
                        serial_number, custodian, device_status
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    row.get("TOOL OF TRADE",""), asset_id, row.get("ASSET NAME",""),
                    row.get("MANUFACTURED DATE",""), row.get("DATE RECEIVED",""),
                    row.get("BUSINESS UNIT",""), row.get("DEPARTMENT",""), row.get("BRANCH",""),
                    row.get("BRAND",""), row.get("ASSET DESCRIPTION",""), serial_number,
                    row.get("CUSTODIAN",""), row.get("ASSET STATUS","")
                ))
                imported_count += 1

            conn.commit()
            messagebox.showinfo(
                "Import Result",
                f"Imported: {imported_count} records\nSkipped (duplicates/empty serial): {skipped_count}"
            )

            refresh_all_comboboxes()
            if refresh_manage_callback:
                refresh_manage_callback()

        except Exception as e:
            return
    # --- Buttons Frame ---
    btn_frame = tk.Frame(tab, bg="#E0DDD9")
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="💾 Save", command=save_to_db, bg="#28b463", fg="white", width=12, height=2)\
        .grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="🧹 Clear", command=clear_form, bg="#e67e22", fg="white", width=12, height=2)\
        .grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="✏️ Manual Entry", command=add_manual_entry, bg="#4e8fe4", fg="white", width=12, height=2)\
        .grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="📂 Import", command=import_file, bg="#9b59b6", fg="white", width=12, height=2)\
        .grid(row=0, column=3, padx=5)

    refresh_all_comboboxes()
    return tab
