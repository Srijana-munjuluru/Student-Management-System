"""
Student Management System — Final Version
Improvements:
- Tkinter + ttk Treeview table with S.No (continuous, no gaps)
- Search by Name (partial) or Roll No (partial)
- Select row → fields pre-fill → update/delete
- Marks validation (0–100)
- Export to CSV
"""

import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import csv

DB_NAME = "students.db"

# --------- Database helpers ----------
def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_no TEXT UNIQUE NOT NULL,
                branch TEXT NOT NULL,
                marks INTEGER NOT NULL CHECK(marks >= 0)
            );
        ''')
        conn.commit()

# --------- App logic ----------
def validate_inputs(name, roll, branch, marks, require_all=True):
    if require_all and not (name and roll and branch and marks):
        messagebox.showwarning("Input Error", "Please fill all fields.")
        return False
    if marks != "":
        try:
            m = int(marks)
            if m < 0 or m > 100:
                messagebox.showerror("Input Error", "Marks must be between 0 and 100.")
                return False
        except ValueError:
            messagebox.showerror("Input Error", "Marks must be an integer.")
            return False
    return True

def add_student():
    name = name_var.get().strip()
    roll = roll_var.get().strip().upper()
    branch = branch_var.get().strip().upper()
    marks = marks_var.get().strip()

    if not validate_inputs(name, roll, branch, marks, require_all=True):
        return

    marks_int = int(marks)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO students (name, roll_no, branch, marks) VALUES (?, ?, ?, ?)",
                (name, roll, branch, marks_int),
            )
            conn.commit()
        messagebox.showinfo("Success", "Student Added Successfully.")
        clear_fields()
        refresh_tree()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Roll Number already exists. Use a unique roll number.")

def refresh_tree(rows=None):
    # Clear existing rows
    for r in tree.get_children():
        tree.delete(r)

    if rows is None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, roll_no, branch, marks FROM students ORDER BY id ASC")
            rows = cursor.fetchall()

    # Insert with continuous serial number (S.No)
    for i, row in enumerate(rows, start=1):
        sno = i  # serial number
        display_row = (sno, row[1], row[2], row[3], row[4])
        tree.insert("", "end", iid=row[0], values=display_row)

def on_tree_select(event):
    sel = tree.selection()
    if not sel:
        return
    iid = sel[0]
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, roll_no, branch, marks FROM students WHERE id=?", (iid,))
        row = cursor.fetchone()
        if row:
            name_var.set(row[1])
            roll_var.set(row[2])
            branch_var.set(row[3])
            marks_var.set(row[4])
            add_btn.config(state="disabled")
            update_btn.config(state="normal")

def clear_fields():
    name_var.set("")
    roll_var.set("")
    branch_var.set("")
    marks_var.set("")
    for s in tree.selection():
        tree.selection_remove(s)
    add_btn.config(state="normal")
    update_btn.config(state="disabled")

def search_students():
    q = search_var.get().strip()
    mode = search_mode.get()
    if q == "":
        refresh_tree()
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        if mode == "Name":
            cursor.execute("SELECT id, name, roll_no, branch, marks FROM students WHERE name LIKE ? ORDER BY id ASC", (f"%{q}%",))
        else:
            cursor.execute("SELECT id, name, roll_no, branch, marks FROM students WHERE roll_no LIKE ? ORDER BY id ASC", (f"%{q.upper()}%",))
        rows = cursor.fetchall()
    refresh_tree(rows)

def update_student():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Selection Error", "Select a record from the table to update.")
        return
    iid = sel[0]
    name = name_var.get().strip()
    roll = roll_var.get().strip().upper()
    branch = branch_var.get().strip().upper()
    marks = marks_var.get().strip()

    if not validate_inputs(name, roll, branch, marks, require_all=True):
        return
    marks_int = int(marks)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE students SET name=?, roll_no=?, branch=?, marks=? WHERE id=?", (name, roll, branch, marks_int, iid))
            conn.commit()
        messagebox.showinfo("Success", "Record updated successfully.")
        clear_fields()
        refresh_tree()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Roll Number already exists for another record.")

def delete_student():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Selection Error", "Select a record from the table to delete.")
        return
    iid = sel[0]
    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected record?")
    if not confirm:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id=?", (iid,))
        conn.commit()
    messagebox.showinfo("Success", "Record deleted.")
    clear_fields()
    refresh_tree()

def export_csv():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, roll_no, branch, marks FROM students ORDER BY id ASC")
        rows = cursor.fetchall()
    if not rows:
        messagebox.showinfo("Export", "No records to export.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["S.No", "Name", "Roll No", "Branch", "Marks"])
        for i, row in enumerate(rows, start=1):
            sno = i
            writer.writerow([sno, row[1], row[2], row[3], row[4]])
    messagebox.showinfo("Export", f"Exported {len(rows)} records to {file_path}")

# --------- GUI Setup ----------
root = tk.Tk()
root.title("Student Management System (Final Version)")
root.geometry("900x600")

# Top Frame - inputs
top_frame = tk.Frame(root, pady=8)
top_frame.pack(fill="x")

name_var = tk.StringVar()
roll_var = tk.StringVar()
branch_var = tk.StringVar()
marks_var = tk.StringVar()
search_var = tk.StringVar()
search_mode = tk.StringVar(value="Name")

tk.Label(top_frame, text="Name").grid(row=0, column=0, padx=6, sticky="e")
tk.Entry(top_frame, textvariable=name_var, width=28).grid(row=0, column=1, padx=6)

tk.Label(top_frame, text="Roll No").grid(row=0, column=2, padx=6, sticky="e")
tk.Entry(top_frame, textvariable=roll_var, width=18).grid(row=0, column=3, padx=6)

tk.Label(top_frame, text="Branch").grid(row=0, column=4, padx=6, sticky="e")
tk.Entry(top_frame, textvariable=branch_var, width=18).grid(row=0, column=5, padx=6)

tk.Label(top_frame, text="Marks").grid(row=0, column=6, padx=6, sticky="e")
tk.Entry(top_frame, textvariable=marks_var, width=8).grid(row=0, column=7, padx=6)

# Buttons
btn_frame = tk.Frame(root, pady=6)
btn_frame.pack(fill="x")

add_btn = tk.Button(btn_frame, text="Add Student", width=14, command=add_student)
add_btn.grid(row=0, column=0, padx=6, pady=4)
update_btn = tk.Button(btn_frame, text="Update Selected", width=14, command=update_student, state="disabled")
update_btn.grid(row=0, column=1, padx=6)
del_btn = tk.Button(btn_frame, text="Delete Selected", width=14, command=delete_student)
del_btn.grid(row=0, column=2, padx=6)
clear_btn = tk.Button(btn_frame, text="Clear", width=14, command=clear_fields)
clear_btn.grid(row=0, column=3, padx=6)
export_btn = tk.Button(btn_frame, text="Export CSV", width=14, command=export_csv)
export_btn.grid(row=0, column=4, padx=6)

# Search area
search_area = tk.Frame(root, pady=4)
search_area.pack(fill="x")
tk.Label(search_area, text="Search").grid(row=0, column=0, padx=6, sticky="e")
tk.Entry(search_area, textvariable=search_var, width=40).grid(row=0, column=1, padx=6)
tk.Radiobutton(search_area, text="By Name", variable=search_mode, value="Name").grid(row=0, column=2, padx=6)
tk.Radiobutton(search_area, text="By Roll", variable=search_mode, value="Roll").grid(row=0, column=3, padx=6)
tk.Button(search_area, text="Search", command=search_students).grid(row=0, column=4, padx=6)
tk.Button(search_area, text="Show All", command=lambda: (search_var.set(""), refresh_tree())).grid(row=0, column=5, padx=6)

# Table (Treeview)
cols = ("S.No", "Name", "Roll No", "Branch", "Marks")
tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
for c in cols:
    tree.heading(c, text=c)
    if c == "S.No":
        tree.column(c, width=60, anchor="center")
    elif c == "Marks":
        tree.column(c, width=80, anchor="center")
    elif c == "Roll No":
        tree.column(c, width=120, anchor="center")
    else:
        tree.column(c, width=220, anchor="w")

vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
tree.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
hsb.grid(row=1, column=0, sticky="ew")
tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# Bind selection
tree.bind("<<TreeviewSelect>>", on_tree_select)

# Initialize DB and populate table
init_db()
refresh_tree()

# Start GUI
root.mainloop()
