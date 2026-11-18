"""Локальное окно генератора с таблицей и копированием."""

import tkinter as tk
from tkinter import font, ttk

from password_gen import DEFAULT_SPECIALS, MAX_COUNT, MAX_LENGTH, PasswordGenerator


BG = "#101923"
PANEL = "#182737"
FIELD = "#0E1925"
BORDER = "#34495A"
INK = "#F2F6FA"
MUTED = "#B3C5D4"
ACCENT = "#70E6C2"
ACCENT_HOVER = "#9AF4D8"
SELECTED = "#245248"
ERROR = "#FFAAA7"


class GeneratorWindow(ttk.Frame):
    def __init__(self, root):
        super().__init__(root, padding=(30, 23, 30, 26), style="Root.TFrame")
        self.root = root
        root.title("Генератор паролей")
        root.geometry("1000x605")
        root.minsize(730, 595)
        root.configure(background=BG)
        self.pack(fill="both", expand=True)
        self.configure_styles()

        self.length = tk.StringVar(root, "16")
        self.count = tk.StringVar(root, "5")
        self.uppercase = tk.BooleanVar(root, True)
        self.lowercase = tk.BooleanVar(root, True)
        self.digits = tk.BooleanVar(root, True)
        self.specials = tk.BooleanVar(root, True)
        self.exclude = tk.BooleanVar(root, True)
        self.special_chars = tk.StringVar(root, DEFAULT_SPECIALS)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text="Генератор паролей", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 19)
        )
        self.build_options()
        self.build_results()
        root.bind("<Return>", self.generate)

    def configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 11), foreground=INK, background=PANEL)
        style.configure("Root.TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Title.TLabel", background=BG, font=("Segoe UI", 26, "bold"))
        style.configure("Section.TLabel", font=("Segoe UI", 15, "bold"))
        style.configure("Hint.TLabel", foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Status.TLabel", foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Error.TLabel", foreground=ERROR, font=("Segoe UI", 10))
        style.configure("TButton", padding=(14, 10), borderwidth=1, relief="flat",
                        background="#274056", foreground=INK, font=("Segoe UI", 11, "bold"))
        style.map("TButton", background=[("disabled", PANEL), ("active", "#365471")],
                  foreground=[("disabled", MUTED)])
        style.configure("Accent.TButton", background=ACCENT, foreground=BG,
                        bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT)
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)])
        for name in ("TEntry", "TSpinbox"):
            style.configure(name, fieldbackground=FIELD, foreground=INK, bordercolor=BORDER,
                            lightcolor=BORDER, darkcolor=BORDER, insertcolor=INK, padding=(8, 6))
            style.map(name, fieldbackground=[("disabled", PANEL)],
                      foreground=[("disabled", MUTED)])
        style.configure("TSpinbox", arrowsize=13, arrowcolor=INK)
        style.configure("TCheckbutton", background=PANEL, foreground=INK, padding=(0, 4),
                        indicatorbackground=FIELD, indicatorforeground=BG)
        style.map("TCheckbutton", background=[("active", PANEL)],
                  indicatorbackground=[("selected", ACCENT)],
                  indicatorforeground=[("selected", BG)])
        style.configure("Passwords.Treeview", background=FIELD, fieldbackground=FIELD,
                        foreground=INK, bordercolor=BORDER, font=("Courier New", 12), rowheight=36)
        style.configure("Passwords.Treeview.Heading", background=PANEL, foreground=MUTED,
                        font=("Segoe UI", 10, "bold"), relief="flat", padding=(8, 7))
        style.map("Passwords.Treeview", background=[("selected", SELECTED)],
                  foreground=[("selected", INK)])
        style.map("Passwords.Treeview.Heading", background=[("active", PANEL)])
        for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            style.configure(name, background="#365471", troughcolor=FIELD, bordercolor=FIELD,
                            lightcolor=FIELD, darkcolor=FIELD, arrowcolor=INK)

    def build_options(self):
        panel = ttk.Frame(self, padding=20, style="Panel.TFrame")
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(8, weight=1)
        ttk.Label(panel, text="Настройки", style="Section.TLabel").grid(row=0, sticky="w")

        numbers = ttk.Frame(panel, style="Panel.TFrame")
        numbers.grid(row=1, sticky="ew", pady=(13, 15))
        for column, (label, limit, variable) in enumerate((
            ("Длина", MAX_LENGTH, self.length), ("Количество", MAX_COUNT, self.count)
        )):
            numbers.columnconfigure(column, weight=1)
            padding = (0, 10) if column == 0 else 0
            ttk.Label(numbers, text=label).grid(row=0, column=column, sticky="w", padx=padding)
            ttk.Spinbox(numbers, from_=1, to=limit, width=6, textvariable=variable).grid(
                row=1, column=column, sticky="ew", padx=padding, pady=(4, 0)
            )
        ttk.Label(panel, text="Группы символов", style="Hint.TLabel").grid(row=2, sticky="w")
        groups = ttk.Frame(panel, style="Panel.TFrame")
        groups.grid(row=3, sticky="ew", pady=(3, 9))
        for index, (label, variable) in enumerate((
            ("Заглавные", self.uppercase), ("Строчные", self.lowercase),
            ("Цифры", self.digits), ("Спецсимволы", self.specials),
        )):
            ttk.Checkbutton(groups, text=label, variable=variable, command=self.refresh_specials).grid(
                row=index // 2, column=index % 2, sticky="w", padx=(0, 12)
            )
        ttk.Label(panel, text="Разрешённые спецсимволы").grid(row=4, sticky="w")
        self.special_entry = ttk.Entry(panel, textvariable=self.special_chars, width=16)
        self.special_entry.grid(row=5, sticky="ew", pady=(4, 10))
        ttk.Checkbutton(panel, text="Исключить похожие символы", variable=self.exclude).grid(
            row=6, sticky="w"
        )
        ttk.Label(panel, text="0, O, 1, I и l", style="Hint.TLabel").grid(row=7, sticky="w", padx=(22, 0))
        ttk.Button(panel, text="Сгенерировать", command=self.generate, style="Accent.TButton").grid(
            row=9, sticky="ew", pady=(14, 0)
        )

    def build_results(self):
        panel = ttk.Frame(self, padding=20, style="Panel.TFrame")
        panel.grid(row=1, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)
        ttk.Label(panel, text="Пароли", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))

        table = ttk.Frame(panel, style="Panel.TFrame")
        table.grid(row=1, column=0, sticky="nsew")
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)
        self.results = ttk.Treeview(table, columns=("number", "password"), show="headings",
                                    selectmode="browse", height=5, style="Passwords.Treeview")
        self.results.heading("number", text="№", anchor="center")
        self.results.heading("password", text="Пароль", anchor="w")
        self.results.column("number", width=54, minwidth=42, anchor="center", stretch=False)
        self.results.column("password", width=390, minwidth=175, anchor="w", stretch=True)
        self.results.grid(row=0, column=0, sticky="nsew")
        self.results.tag_configure("even", background="#152536")
        yscroll = ttk.Scrollbar(table, orient="vertical", command=self.results.yview)
        xscroll = ttk.Scrollbar(table, orient="horizontal", command=self.results.xview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        self.results.configure(
            yscrollcommand=lambda first, last: self.set_scrollbar(yscroll, first, last),
            xscrollcommand=lambda first, last: self.set_scrollbar(xscroll, first, last),
        )
        self.results.bind("<<TreeviewSelect>>", self.update_copy_button)
        self.results.bind("<Control-c>", self.copy_selected)

        self.copy_button = ttk.Button(panel, text="Копировать выбранный", command=self.copy_selected, state="disabled")
        self.copy_button.grid(row=2, column=0, sticky="w", pady=(14, 0))
        self.status = ttk.Label(panel, text="Нажми «Сгенерировать», чтобы получить пароли.",
                                style="Status.TLabel", wraplength=345, justify="left")
        self.status.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    @staticmethod
    def set_scrollbar(scrollbar, first, last):
        scrollbar.set(first, last)
        if float(first) == 0.0 and float(last) == 1.0:
            scrollbar.grid_remove()
        else:
            scrollbar.grid()

    def refresh_specials(self):
        self.special_entry.state(["!disabled" if self.specials.get() else "disabled"])

    def update_copy_button(self, _event=None):
        self.copy_button.state(["!disabled" if self.results.selection() else "disabled"])

    def generate(self, _event=None):
        try:
            length = int(self.length.get())
            count = int(self.count.get())
        except ValueError:
            self.status.configure(text="Введи целые числа для длины и количества.", style="Error.TLabel")
            return "break"
        generator = PasswordGenerator(length=length, uppercase=self.uppercase.get(), lowercase=self.lowercase.get(),
                                      digits=self.digits.get(), specials=self.specials.get(),
                                      exclude_ambiguous=self.exclude.get(), special_chars=self.special_chars.get())
        try:
            passwords = generator.generate(count)
        except ValueError as exc:
            self.status.configure(text=str(exc), style="Error.TLabel")
            return "break"

        self.results.delete(*self.results.get_children())
        character_width = font.Font(root=self.root, font=("Courier New", 12)).measure("M")
        minimum = max(175, length * character_width + 18)
        available = self.results.winfo_width() - self.results.column("number", "width") - 4
        self.results.column("password", minwidth=minimum, width=max(minimum, available))
        for number, password in enumerate(passwords, start=1):
            self.results.insert("", "end", values=(number, password), tags=("even",) if number % 2 == 0 else ())
        first = self.results.get_children()[0]
        self.results.selection_set(first)
        self.results.focus(first)
        self.results.xview_moveto(0)
        self.update_copy_button()
        self.status.configure(text=f"Паролей сгенерировано — {len(passwords)}. Выбрана первая строка.",
                              style="Status.TLabel")
        return "break"

    def copy_selected(self, _event=None):
        selected = self.results.selection()
        if selected:
            password = self.results.set(selected[0], "password")
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            self.status.configure(text="Выбранный пароль скопирован.", style="Status.TLabel")
        return "break"


def main():
    root = tk.Tk()
    GeneratorWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
