import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from book_print import print_book_dialog

# ==============================================================================
#  THEMES
#  To add a new theme, just copy one of these blocks, change the name,
#  and edit the colours. That's it.
# ==============================================================================
THEMES = {
    "dark": {
        "bg":      "#1e1e1e",   # main window background
        "fg":      "#e0e0e0",   # text colour
        "editor":  "#252526",   # editor box background
        "sidebar": "#2d2d2d",   # toolbar background
        "accent":  "#0078d4",   # highlight / button accent
        "border":  "#3c3c3c",   # thin border around editor
        "btn":     "#3c3c3c",   # button background
        "btn_fg":  "#e0e0e0",   # button text
        "select":  "#264f78",   # text selection colour
    },
    "light": {
        "bg":      "#f5f5f5",
        "fg":      "#1e1e1e",
        "editor":  "#ffffff",
        "sidebar": "#e8e8e8",
        "accent":  "#0078d4",
        "border":  "#cccccc",
        "btn":     "#e0e0e0",
        "btn_fg":  "#1e1e1e",
        "select":  "#cce4f7",
    },
    "pink": {
        "bg":      "#ffb8ec",
        "fg":      "#6b2d4e",
        "editor":  "#fff0f7",
        "sidebar": "#f7c5df",
        "accent":  "#c2185b",
        "border":  "#f48fb1",
        "btn":     "#f48fb1",
        "btn_fg":  "#6b2d4e",
        "select":  "#f8bbd0",
    },
    "green": {
        "bg":      "#1a2b1a",
        "fg":      "#c8e6c9",
        "editor":  "#1e331e",
        "sidebar": "#243424",
        "accent":  "#4caf50",
        "border":  "#2e472e",
        "btn":     "#2e472e",
        "btn_fg":  "#c8e6c9",
        "select":  "#33691e",
    },
    "mustard": {
        "bg":      "#fcd15b",
        "fg":      "#856e30",
        "editor":  "#5c5134",
        "sidebar": "#5c5134",
        "accent":  "#667800",
        "border":  "#a1a877",
        "btn":     "#bbc969",
        "btn_fg":  "#49521a",
        "select":  "#917d57",
    },
}


THEME_ORDER = ["dark", "light", "pink", "green", "mustard"]


FONT_FAMILIES = ["Georgia", "Times New Roman", "Courier New", "Arial",
                 "Helvetica", "Verdana", "Palatino", "Garamond", "Minecraft"]
FONT_SIZES = [10, 11, 12, 13, 14, 16, 18, 20, 22, 24]


class EditorWindow(tk.Toplevel):
    def __init__(self, master, book_data, filepath, theme_name, on_save_callback):
        super().__init__(master)

      
        self.book = book_data
        self.filepath = filepath
        self.cur_page = 0
        self.unsaved = False
        self.on_save = on_save_callback
        self.theme = THEMES[theme_name]

        self.title(self.book["title"])
        self.geometry("500x1000")
        self.minsize(700, 500)
        self.configure(bg=self.theme["bg"])

        self._build_toolbar()
        self._build_editor()
        self._build_nav_bar()
        self._load_page(0)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    
    def _build_toolbar(self):
        t = self.theme
        bar = tk.Frame(self, bg=t["sidebar"], pady=4)
        bar.pack(side=tk.TOP, fill=tk.X)

        def toolbar_btn(label, action):
            tk.Button(bar, text=label, command=action,
                      bg=t["btn"], fg=t["btn_fg"],
                      relief=tk.FLAT, padx=10, pady=3,
                      cursor="hand2").pack(side=tk.LEFT, padx=3)

        toolbar_btn("💾",  self.save)
        toolbar_btn("+",   self._add_page)
        toolbar_btn("−",   self._del_page)

        tk.Label(bar, text="  Font:", bg=t["sidebar"], fg=t["fg"]).pack(side=tk.LEFT)
        self.font_var = tk.StringVar(value="Georgia")
        font_picker = ttk.Combobox(bar, textvariable=self.font_var,
                                   values=FONT_FAMILIES, width=14, state="readonly")
        font_picker.pack(side=tk.LEFT, padx=(0, 6))
        font_picker.bind("<<ComboboxSelected>>", lambda _: self._apply_font())
        tk.Label(bar, text="Size:", bg=t["sidebar"], fg=t["fg"]).pack(side=tk.LEFT)
        self.size_var = tk.IntVar(value=13)
        size_picker = ttk.Combobox(bar, textvariable=self.size_var,
                                   values=FONT_SIZES, width=4, state="readonly")
        size_picker.pack(side=tk.LEFT, padx=(0, 6))
        size_picker.bind("<<ComboboxSelected>>", lambda _: self._apply_font())

        self.page_label = tk.Label(bar, text="", bg=t["sidebar"], fg=t["fg"])
        self.page_label.pack(side=tk.RIGHT, padx=10)

    def _build_editor(self):
        t = self.theme

        border = tk.Frame(self, bg=t["border"], padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.text = tk.Text(
            border,
            bg=t["editor"], fg=t["fg"],
            insertbackground=t["fg"],     # colour
            selectbackground=t["select"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            undo=True,
            padx=16, pady=16,
            font=(self.font_var.get(), self.size_var.get()),
        )

        scrollbar = tk.Scrollbar(border, command=self.text.yview,
                                 bg=t["sidebar"], troughcolor=t["bg"])
        self.text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.bind("<<Modified>>", self._on_text_modified)

    def _build_nav_bar(self):
        t = self.theme
        nav = tk.Frame(self, bg=t["bg"])
        nav.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Button(nav, text="◀ Prev", command=self._prev_page,
                  bg=t["btn"], fg=t["btn_fg"], relief=tk.FLAT,
                  padx=10, pady=4).pack(side=tk.LEFT, padx=4, pady=4)

        tk.Button(nav, text="Next ▶", command=self._next_page,
                  bg=t["btn"], fg=t["btn_fg"], relief=tk.FLAT,
                  padx=10, pady=4).pack(side=tk.LEFT, padx=4, pady=4)

    def _apply_font(self):
        self.text.config(font=(self.font_var.get(), self.size_var.get()))

    def _update_page_label(self):
        total = len(self.book["pages"])
        self.page_label.config(text=f"Page {self.cur_page + 1} / {total}")

    def _save_current_text(self):
        if hasattr(self, "text"):
            self.book["pages"][self.cur_page] = self.text.get("1.0", "end-1c")

    def _load_page(self, index):
        self._save_current_text()
        self.cur_page = index
        self.text.edit_modified(False)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", self.book["pages"][index])
        self.text.edit_modified(False)
        self._update_page_label()

    def _prev_page(self):
        if self.cur_page > 0:
            self._load_page(self.cur_page - 1)

    def _next_page(self):
        if self.cur_page < len(self.book["pages"]) - 1:
            self._load_page(self.cur_page + 1)

    def _add_page(self):
        self._save_current_text()
        self.book["pages"].insert(self.cur_page + 1, "")
        self._load_page(self.cur_page + 1)

    def _del_page(self):
        if len(self.book["pages"]) == 1:
            messagebox.showwarning("Can't delete", "A book needs at least one page.", parent=self)
            return
        if messagebox.askyesno("Delete page", f"Delete page {self.cur_page + 1}?", parent=self):
            self.book["pages"].pop(self.cur_page)
            new_index = max(0, self.cur_page - 1)
            self.cur_page = new_index
            self.text.delete("1.0", tk.END)
            self._load_page(new_index)

    def save(self):
        self._save_current_text()
        if not self.filepath:
            self.filepath = filedialog.asksaveasfilename(
                defaultextension=".book",
                filetypes=[("Book files", "*.book"), ("All files", "*.*")],
                parent=self,
            )
            if not self.filepath:
                return
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.book, f, ensure_ascii=False, indent=2)
        self.unsaved = False
        self.title(self.book["title"])
        self.on_save(self.filepath, self.book["title"])

    def _on_text_modified(self, _event=None):
        if self.text.edit_modified():
            self.unsaved = True
            self.title(f"* {self.book['title']}")

    def _on_close(self):
        self._save_current_text()
        if self.unsaved:
            answer = messagebox.askyesnocancel("Unsaved changes!!!",
                                               "Save before closing?", parent=self)
            if answer is None:
                return
            if answer:
                self.save()
        self.destroy()

    def apply_theme(self, theme_name):
        self.theme = THEMES[theme_name]
        t = self.theme
        self.configure(bg=t["bg"])
        self.text.config(bg=t["editor"], fg=t["fg"],
                         insertbackground=t["fg"],
                         selectbackground=t["select"])


#  LAUNCHER WINDOW
class BookWriter(tk.Tk):
    def __init__(self):
        super().__init__()

        self.theme_index = 0   
        self.theme_name = THEME_ORDER[self.theme_index]
        self.open_editors = []

        self.title("BookWriter")
        self.geometry("500x400")
        self.resizable(True, True)

        self._build_menu()
        self._build_launcher_ui()

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Book",        command=self._new_book)
        file_menu.add_command(label="Open Book",       command=self._open_book)
        file_menu.add_separator()
        file_menu.add_command(label="Print to PDF",    command=lambda: print_book_dialog(self))
        file_menu.add_separator()
        file_menu.add_command(label="Quit",            command=self.quit)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Cycle Theme",     command=self._cycle_theme)

  
    def _build_launcher_ui(self):
        t = THEMES[self.theme_name]
        self.configure(bg=t["bg"])

        for widget in self.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()

        tk.Label(self, text="📖 BookMKR v1.0",
                 font=("Georgia", 24, "bold"),
                 bg=t["bg"], fg=t["fg"]).pack(pady=(30, 4))

        tk.Label(self, text="Release 1.0",
                 font=("Georgia", 6, "bold"),
                 bg=t["bg"], fg=t["accent"]).pack(pady=(0, 28))

        def big_btn(label, action):
            tk.Button(self, text=label, command=action,
                      bg=t["btn"], fg=t["btn_fg"],
                      relief=tk.FLAT, width=24, pady=9,
                      font=("Georgia", 11), cursor="hand2").pack(pady=5)

        big_btn("🕮  New Book",       self._new_book)
        big_btn("📂  Open Book",     self._open_book)
        big_btn("🖨  Print to PDF",  lambda: print_book_dialog(self))
        big_btn("🎨  Theme Toggle",   self._cycle_theme)

        tk.Label(self, text=f"Theme: {self.theme_name}",
                 font=("Georgia", 9),
                 bg=t["bg"], fg=t["border"]).pack(pady=(16, 0))

    def _cycle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEME_ORDER)
        self.theme_name = THEME_ORDER[self.theme_index]
        self._build_launcher_ui()
        for editor in self.open_editors:
            if editor.winfo_exists():
                editor.apply_theme(self.theme_name)

    def _new_book(self):
        title = self._ask_for_title()
        if not title:
            return
        book = {"title": title, "pages": [""]}
        self._open_editor(book, filepath=None)

    def _open_book(self):
        path = filedialog.askopenfilename(
            filetypes=[("Book files", "*.book"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                book = json.load(f)
            if "pages" not in book:
                raise ValueError("Not a valid .book file")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")
            return
        self._open_editor(book, filepath=path)

    def _ask_for_title(self):
        t = THEMES[self.theme_name]
        dlg = tk.Toplevel(self)
        dlg.title("New Book")
        dlg.geometry("320x135")
        dlg.resizable(False, False)
        dlg.configure(bg=t["bg"])
        dlg.grab_set()

        tk.Label(dlg, text="Book title:",
                 bg=t["bg"], fg=t["fg"],
                 font=("Georgia", 11)).pack(pady=(18, 4))

        entry = tk.Entry(dlg, bg=t["editor"], fg=t["fg"],
                         insertbackground=t["fg"],
                         relief=tk.FLAT, font=("Georgia", 11), width=28)
        entry.pack(pady=4)
        entry.focus()

        result = [None]

        def confirm(_=None):
            result[0] = entry.get().strip() or "Untitled Book"
            dlg.destroy()

        entry.bind("<Return>", confirm)
        tk.Button(dlg, text="Create", command=confirm,
                  bg=t["accent"], fg="white",
                  relief=tk.FLAT, padx=14, pady=4).pack(pady=8)

        self.wait_window(dlg)
        return result[0]

    def _open_editor(self, book, filepath):
        editor = EditorWindow(self, book, filepath, self.theme_name,
                              on_save_callback=lambda path, title: None)
        self.open_editors.append(editor)


if __name__ == "__main__":
    app = BookWriter()
    app.mainloop()
