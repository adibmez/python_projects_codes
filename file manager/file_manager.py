import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import platform


class FileManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Python File Manager")
        self.root.geometry("800x600")

        # Dark mode colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.list_bg = "#252526"
        self.select_bg = "#37373d"

        self.root.configure(bg=self.bg_color)

        self.current_path = os.getcwd()

        self.create_widgets()
        self.refresh_file_list()

    def create_widgets(self):
        # Top bar
        top_frame = tk.Frame(self.root, bg=self.bg_color)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.up_button = tk.Button(top_frame, text="⬆ Up", command=self.go_up,
                                   bg=self.select_bg, fg=self.fg_color, relief=tk.FLAT)
        self.up_button.pack(side=tk.LEFT, padx=(0, 10))

        self.path_label = tk.Label(top_frame, text=self.current_path,
                                   bg=self.bg_color, fg=self.fg_color, font=("Arial", 10))
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # File list
        list_frame = tk.Frame(self.root, bg=self.list_bg)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(list_frame, columns=("Size", "Type"), show="headings")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Type", text="Type")

        # Style for Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.list_bg,
                        foreground=self.fg_color, fieldbackground=self.list_bg, borderwidth=0)
        style.map("Treeview", background=[('selected', self.select_bg)])

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_file_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.path_label.config(text=self.current_path)

        try:
            items = os.listdir(self.current_path)
            items.sort(key=lambda x: os.path.isdir(os.path.join(self.current_path, x)), reverse=True)

            for item in items:
                full_path = os.path.join(self.current_path, item)
                is_dir = os.path.isdir(full_path)

                size = ""
                if not is_dir:
                    try:
                        size = f"{os.path.getsize(full_path) / 1024:.1f} KB"
                    except OSError:
                        size = "N/A"

                item_type = "Folder" if is_dir else "File"

                # Insert with text as the filename (first column usually, but we use headings)
                # Treeview default column '#0' is hidden with show="headings" if we don't want it,
                # but here we want the name. Let's adjust columns.
                # Actually, let's use #0 for name.

                self.tree.insert("", tk.END, text=item, values=(size, item_type))

        except PermissionError:
            messagebox.showerror("Error", "Permission Denied")

    # Fix Treeview columns to show Name
    def create_widgets(self):
        # Top bar
        top_frame = tk.Frame(self.root, bg=self.bg_color)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.up_button = tk.Button(top_frame, text="⬆ Up", command=self.go_up,
                                   bg=self.select_bg, fg=self.fg_color, relief=tk.FLAT)
        self.up_button.pack(side=tk.LEFT, padx=(0, 10))

        self.path_label = tk.Label(top_frame, text=self.current_path,
                                   bg=self.bg_color, fg=self.fg_color, font=("Arial", 10))
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # File list
        list_frame = tk.Frame(self.root, bg=self.list_bg)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(list_frame, columns=("Name", "Size", "Type"), show="headings")
        self.tree.heading("Name", text="Name", anchor=tk.W)
        self.tree.heading("Size", text="Size", anchor=tk.W)
        self.tree.heading("Type", text="Type", anchor=tk.W)

        self.tree.column("Name", width=400)
        self.tree.column("Size", width=100)
        self.tree.column("Type", width=100)

        # Style for Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.list_bg,
                        foreground=self.fg_color, fieldbackground=self.list_bg, borderwidth=0)
        style.configure("Treeview.Heading", background=self.select_bg, foreground=self.fg_color, relief="flat")
        style.map("Treeview", background=[('selected', self.select_bg)])

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_file_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.path_label.config(text=self.current_path)

        try:
            items = os.listdir(self.current_path)
            # Sort: Directories first, then files
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x.lower()))

            for item in items:
                full_path = os.path.join(self.current_path, item)
                is_dir = os.path.isdir(full_path)

                size = ""
                if not is_dir:
                    try:
                        size = f"{os.path.getsize(full_path) / 1024:.1f} KB"
                    except OSError:
                        size = "N/A"

                item_type = "Folder" if is_dir else "File"

                self.tree.insert("", tk.END, values=(item, size, item_type))

        except PermissionError:
            messagebox.showerror("Error", "Permission Denied")

    def go_up(self):
        parent_path = os.path.dirname(self.current_path)
        if parent_path != self.current_path:
            self.current_path = parent_path
            self.refresh_file_list()

    def on_double_click(self, event):
        item_id = self.tree.selection()[0]
        item_values = self.tree.item(item_id, "values")
        item_name = item_values[0]

        full_path = os.path.join(self.current_path, item_name)

        if os.path.isdir(full_path):
            self.current_path = full_path
            self.refresh_file_list()
        else:
            self.open_file(full_path)

    def open_file(self, filepath):
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', filepath))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(filepath)
            else:  # linux variants
                subprocess.call(('xdg-open', filepath))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileManager(root)
    root.mainloop()
