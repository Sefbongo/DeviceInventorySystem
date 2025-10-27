import tkinter as tk
from tkinter import ttk
from db import get_inventory_conn

def build_reports_tab(root, notebook):
    """
    Reports tab: Summary metrics + interactive records Treeview
    Includes a dropdown for branches.
    Display style matches Manage Devices tab with color-coded device_status.
    Returns the tab and refresh_reports callback for auto-refresh.
    """

    conn = get_inventory_conn()
    cursor = conn.cursor()
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="📊 REPORTS")

    frame = ttk.LabelFrame(tab, text="Inventory Summary", padding=15)
    frame.pack(fill="both", expand=False, padx=20, pady=10)

    stats_tree = ttk.Treeview(frame, columns=("DEVICE STATUS", "COUNT"), show="headings", height=12)
    stats_tree.heading("DEVICE STATUS", text="DEVICE STATUS")
    stats_tree.heading("COUNT", text="COUNT")
    stats_tree.column("DEVICE STATUS", width=300)
    stats_tree.column("COUNT", width=100, anchor="center")
    stats_tree.pack(fill="both", expand=True, side="left")

    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=stats_tree.yview)
    stats_tree.configure(yscroll=scroll_y.set)
    scroll_y.pack(side="right", fill="y")

    branch_frame = ttk.LabelFrame(tab, text="Select Branch", padding=10)
    branch_frame.pack(fill="x", expand=False, padx=20, pady=5)

    branch_var = tk.StringVar()
    branch_combo = ttk.Combobox(branch_frame, textvariable=branch_var, state="readonly", width=30)
    branch_combo.pack(pady=5)
    branch_combo.set("Select Branch")


    records_frame = ttk.LabelFrame(tab, text="Matching Records", padding=10)
    records_frame.pack(fill="both", expand=True, padx=20, pady=10)

    HEADERS = [
        "ID", "TOOL OF TRADE", "ASSET ID", "ASSET NAME", "MANUFACTURED DATE", "DATE ACQUIRED",
        "BUSINESS UNIT", "DEPARTMENT", "BRANCH", "BRAND", "ASSET DESCRIPTION",
        "SERIAL NUMBER", "CUSTODIAN", "ASSET STATUS"
    ]

    records_tree = ttk.Treeview(records_frame, columns=HEADERS, show="headings", height=18)
    for col in HEADERS:
        records_tree.heading(col, text=col)
        records_tree.column(col, width=120, stretch=True)
    records_tree.pack(fill="both", expand=True, side="left")

    scroll_y2 = ttk.Scrollbar(records_frame, orient="vertical", command=records_tree.yview)
    records_tree.configure(yscroll=scroll_y2.set)
    scroll_y2.pack(side="right", fill="y")


    metric_queries = {
        "TOTAL DEVICE ACTIVE": "SELECT * FROM inventory WHERE cancelled=0 AND device_status='ACTIVE'OR device_status= 'FOR REPLACEMENT'",
        "TOTAL CANCELLED ENTRIES": "SELECT * FROM inventory WHERE cancelled=1",
        "TOTAL DEVICE UNDER HEAD OFFICE": "SELECT * FROM inventory WHERE cancelled=0 AND branch='HOME OFFICE'",
        "TOTAL DEVICE FOR REPLACEMENT": "SELECT * FROM inventory WHERE cancelled=0 AND device_status='FOR REPLACEMENT'",
        "TOTAL DEVICE FOR REPAIR": "SELECT * FROM inventory WHERE cancelled=0 AND device_status='FOR REPAIR'",
        "TOTAL DEVICE FOR RETIRED": "SELECT * FROM inventory WHERE cancelled=0 AND device_status='RETIRED'",
        "TOTAL DEVICE FOR DISPOSAL": "SELECT * FROM inventory WHERE cancelled=0 AND device_status='FOR DISPOSAL'",
    }

    def refresh_reports():
    # Use a fresh connection every refresh
        conn = get_inventory_conn()
        cursor = conn.cursor()

    # Clear previous stats
    stats_tree.delete(*stats_tree.get_children())
    for metric, query in metric_queries.items():
        cursor.execute(query)
        rows = cursor.fetchall()
        stats_tree.insert("", "end", values=(metric, len(rows)))

    # Update branch list
    cursor.execute("SELECT DISTINCT branch FROM inventory WHERE cancelled=0 ORDER BY branch")
    branches = [r[0] for r in cursor.fetchall() if r[0]]
    branch_combo['values'] = branches
    if branches:
        branch_combo.set("Select Branch")

    # Clear records tree
    records_tree.delete(*records_tree.get_children())

    # Close this refresh connection


    def on_tree_click(event):
        selected = stats_tree.focus()
        if not selected:
            return
        metric_name = stats_tree.item(selected, "values")[0]
        query = metric_queries.get(metric_name)
        if query:
            cursor.execute(query)
            records = cursor.fetchall()
            display_records(records)

    def on_branch_select(event):
        selected_branch = branch_var.get()
        if not selected_branch:
            return
        cursor.execute("SELECT * FROM inventory WHERE cancelled=0 AND branch=?", (selected_branch,))
        records = cursor.fetchall()
        display_records(records)

    def display_records(records):
        records_tree.delete(*records_tree.get_children())
        for r in records:
            tag = ""
            status = r[13].upper() 
            if status == "FOR REPLACEMENT":
                tag = "FOR REPLACEMENT"
            elif status == "FOR REPAIR":
                tag = "FOR REPAIR"
            elif status == "RETIRED":
                tag = "RETIRED"
            elif status == "FOR DISPOSAL":
                tag = "FOR DISPOSAL"
            elif status == "ACTIVE":
                tag = "ACTIVE"

            records_tree.insert("", "end", values=r, tags=(tag,))

        records_tree.tag_configure("FOR REPLACEMENT", background="#f9e79f")  
        records_tree.tag_configure("FOR REPAIR", background="#546d0f")       
        records_tree.tag_configure("RETIRED", background="#11a4ee")      
        records_tree.tag_configure("FOR DISPOSAL", background="#f5b7b1")    
        records_tree.tag_configure("ACTIVE", background="#02db4a")  

    stats_tree.bind("<ButtonRelease-1>", on_tree_click)
    branch_combo.bind("<<ComboboxSelected>>", on_branch_select)

    refresh_reports()

    return tab, refresh_reports
