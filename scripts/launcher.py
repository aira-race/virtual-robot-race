# launcher.py
# ============================================================
# GUI Launcher for Virtual Robot Race - Beta 1.7
# Shown when HEADLESS=0. Lets the user review/edit config before starting.
# Writes any changes back to config.txt, then returns True (start) or False (quit).
# ============================================================

import tkinter as tk
from tkinter import messagebox
import re
from pathlib import Path

# ── Color palette (aira brand) ────────────────────────────────────────────────
BG      = "#080C14"   # Deep Navy — window background
SURFACE = "#0D1420"   # Panel / input background
BORDER  = "#1A2540"   # Borders / dividers
ACCENT  = "#00D4FF"   # Electric Cyan — START button, logo
AMBER   = "#FF8C00"   # Amber — section labels, version, top line
TEXT    = "#E8EEF8"   # Primary text (values)
MUTED   = "#4A5878"   # Secondary text (labels)
ON_BG   = "#001F2D"   # Toggle ON background
ON_FG   = "#00D4FF"   # Toggle ON foreground (Cyan)
OFF_FG  = "#4A5878"   # Toggle OFF foreground (Muted)

FONT_UI   = ("Courier", 9)
FONT_BOLD = ("Courier", 10, "bold")
FONT_MONO = ("Courier", 10)
FONT_TITLE= ("Courier", 16, "bold")

MODE_OPTIONS = ["keyboard", "table", "rule_based", "ai", "smartphone"]
MODE_TO_NUM  = {"keyboard": "1", "table": "2", "rule_based": "3",
                "ai": "4", "smartphone": "5"}
NUM_TO_MODE  = {v: k for k, v in MODE_TO_NUM.items()}

CONFIG_PATH = Path("config.txt")


# ── Config I/O ────────────────────────────────────────────────────────────────

def _read_config() -> dict:
    cfg = {}
    if CONFIG_PATH.exists():
        for line in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.split("#")[0].strip()
    return cfg


def _write_config_value(key: str, value: str) -> None:
    """Update a single KEY=value line in config.txt, preserving all comments."""
    text = CONFIG_PATH.read_text(encoding="utf-8")
    pattern = rf"^({re.escape(key)}\s*=\s*).*$"
    new_text = re.sub(pattern, rf"\g<1>{value}", text, flags=re.MULTILINE)
    CONFIG_PATH.write_text(new_text, encoding="utf-8")


# ── Widgets ───────────────────────────────────────────────────────────────────

def _entry(parent, var) -> tk.Entry:
    return tk.Entry(
        parent, textvariable=var, bg=SURFACE, fg=TEXT,
        insertbackground=TEXT, relief="flat", font=FONT_MONO,
        highlightthickness=1, highlightbackground=BORDER,
        highlightcolor=ACCENT, bd=4,
    )


def _dropdown(parent, var, options) -> tk.Frame:
    """Styled OptionMenu on a flat dark background."""
    f = tk.Frame(parent, bg=SURFACE, highlightthickness=1,
                 highlightbackground=BORDER)
    m = tk.OptionMenu(f, var, *options)
    m.configure(
        bg=SURFACE, fg=TEXT, activebackground=BORDER, activeforeground=ACCENT,
        relief="flat", font=FONT_MONO, bd=0, highlightthickness=0,
        indicatoron=True, width=14,
    )
    m["menu"].configure(
        bg=SURFACE, fg=TEXT, activebackground=BORDER,
        activeforeground=ACCENT, font=FONT_MONO,
    )
    m.pack(fill="x")
    return f


def _section(parent, label: str) -> None:
    tk.Label(parent, text=label, bg=BG, fg=AMBER,
             font=("Courier", 8), anchor="w").pack(fill="x", padx=24, pady=(16, 2))


def _row(parent, label: str, widget_fn) -> None:
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", padx=24, pady=5)
    tk.Label(row, text=label, bg=BG, fg=MUTED,
             font=FONT_UI, width=13, anchor="w").pack(side="left")
    widget_fn(row).pack(side="left", fill="x", expand=True)


def _toggle(parent, var, on_label: str, off_label: str) -> tk.Button:
    """A flat button that toggles between ON/OFF states."""
    btn = tk.Button(parent, relief="flat", bd=0, padx=12, pady=3,
                    cursor="hand2", font=FONT_UI)

    def refresh():
        if var.get():
            btn.configure(text=on_label, bg=ON_BG, fg=ON_FG,
                          activebackground=ON_BG, activeforeground=ON_FG)
        else:
            btn.configure(text=off_label, bg=SURFACE, fg=OFF_FG,
                          activebackground=SURFACE, activeforeground=MUTED)

    btn.configure(command=lambda: [var.set(1 - var.get()), refresh()])
    refresh()
    return btn


# ── Main launcher ─────────────────────────────────────────────────────────────

def show_launcher() -> bool:
    """
    Display the launcher window.
    Returns True if the user clicked START (config.txt updated),
    or False if the user closed / clicked QUIT.
    """
    cfg = _read_config()
    result = {"start": False}

    root = tk.Tk()
    root.title("Virtual Robot Race")
    root.configure(bg=BG)
    root.resizable(False, False)

    # Center on screen
    W, H = 420, 490
    root.update_idletasks()
    x = (root.winfo_screenwidth()  - W) // 2
    y = (root.winfo_screenheight() - H) // 2
    root.geometry(f"{W}x{H}+{x}+{y}")

    # ── Amber accent line (top) ────────────────────────────────
    tk.Frame(root, bg=AMBER, height=2).pack(fill="x")

    # ── Title bar ─────────────────────────────────────────────
    title_bar = tk.Frame(root, bg=BG)
    title_bar.pack(fill="x")
    tk.Label(title_bar, text="aira", bg=BG, fg=ACCENT,
             font=FONT_TITLE, padx=24, pady=12, anchor="w").pack(side="left")
    tk.Label(title_bar, text="Beta 1.7", bg=BG, fg=AMBER,
             font=FONT_UI, padx=24).pack(side="right", anchor="s", pady=14)

    # ── Player ────────────────────────────────────────────────
    _section(root, "PLAYER")
    name_var = tk.StringVar(value=cfg.get("NAME", "Player0000"))
    comp_var = tk.StringVar(value=cfg.get("COMP_NAME", "RACE_XXXX"))
    _row(root, "Name",        lambda p: _entry(p, name_var))
    _row(root, "Competition", lambda p: _entry(p, comp_var))

    # ── Robots ────────────────────────────────────────────────
    _section(root, "ROBOTS")
    active_var = tk.StringVar(value=cfg.get("ACTIVE_ROBOTS", "1"))
    r1_var = tk.StringVar(value=NUM_TO_MODE.get(cfg.get("R1_MODE_NUM", "3"), "rule_based"))
    r2_var = tk.StringVar(value=NUM_TO_MODE.get(cfg.get("R2_MODE_NUM", "4"), "ai"))

    # Store references to R1/R2 dropdown frames for enable/disable
    r1_widgets = []
    r2_widgets = []

    def update_robot_state(*_):
        """Enable/disable R1 and R2 mode selectors based on ACTIVE_ROBOTS."""
        active = active_var.get()
        r1_on = active in ("1", "1,2")
        r2_on = active in ("2", "1,2")
        for w in r1_widgets:
            w.configure(highlightbackground=BORDER if r1_on else BG)
            for child in w.winfo_children():
                child.configure(state="normal" if r1_on else "disabled",
                                fg=TEXT if r1_on else MUTED)
        for w in r2_widgets:
            w.configure(highlightbackground=BORDER if r2_on else BG)
            for child in w.winfo_children():
                child.configure(state="normal" if r2_on else "disabled",
                                fg=TEXT if r2_on else MUTED)

    active_var.trace_add("write", update_robot_state)

    def _dropdown_tracked(parent, var, options, store):
        f = _dropdown(parent, var, options)
        store.append(f)
        return f

    _row(root, "Active",  lambda p: _dropdown(p, active_var, ["1", "2", "1,2"]))
    _row(root, "R1 mode", lambda p: _dropdown_tracked(p, r1_var, MODE_OPTIONS, r1_widgets))
    _row(root, "R2 mode", lambda p: _dropdown_tracked(p, r2_var, MODE_OPTIONS, r2_widgets))

    # Apply initial state after widgets are created
    root.after(10, update_robot_state)

    # ── Run options ───────────────────────────────────────────
    _section(root, "RUN OPTIONS")
    data_var = tk.IntVar(value=int(cfg.get("DATA_SAVE", "0")))
    race_var = tk.IntVar(value=int(cfg.get("RACE_FLAG", "0")))
    _row(root, "Data save",  lambda p: _toggle(p, data_var, "ON", "OFF"))
    _row(root, "Race flag",  lambda p: _toggle(p, race_var, "SUBMIT", "TEST ONLY"))

    # ── Buttons ───────────────────────────────────────────────
    tk.Frame(root, bg=BG).pack(fill="both", expand=True)  # spacer

    btn_frame = tk.Frame(root, bg=BG, padx=24, pady=18)
    btn_frame.pack(fill="x")

    def on_start():
        name = name_var.get().strip()
        if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", name):
            messagebox.showerror(
                "Invalid Name",
                "Name must be 1–16 characters: A-Z, a-z, 0-9, or _ (underscore).",
                parent=root,
            )
            return
        # Check: keyboard mode not allowed in competition mode
        comp = comp_var.get().strip()
        is_comp = (race_var.get() == 1 and comp not in ("", "Tutorial"))
        active = active_var.get()
        keyboard_robots = [
            r for r, v in [("R1", r1_var.get()), ("R2", r2_var.get())]
            if v == "keyboard" and r[1] in active.replace(",", "")
        ]
        if is_comp and keyboard_robots:
            messagebox.showerror(
                "Invalid Configuration",
                f"{', '.join(keyboard_robots)} is set to Keyboard mode,\n"
                f"but COMP_NAME='{comp}' (competition mode).\n\n"
                "Keyboard mode cannot participate in competitions.\n"
                "Change the mode, or set Race Flag to OFF.",
                parent=root,
            )
            return
        _write_config_value("NAME",          name)
        _write_config_value("COMP_NAME",     comp_var.get().strip())
        _write_config_value("ACTIVE_ROBOTS", active_var.get())
        _write_config_value("R1_MODE_NUM",   MODE_TO_NUM[r1_var.get()])
        _write_config_value("R2_MODE_NUM",   MODE_TO_NUM[r2_var.get()])
        _write_config_value("DATA_SAVE",     str(data_var.get()))
        _write_config_value("RACE_FLAG",     str(race_var.get()))
        result["start"] = True
        root.destroy()

    def on_quit():
        root.destroy()

    tk.Button(
        btn_frame, text="QUIT", command=on_quit,
        bg=BORDER, fg=MUTED, relief="flat", font=FONT_UI,
        padx=20, pady=8, cursor="hand2",
        activebackground=BORDER, activeforeground=TEXT,
    ).pack(side="left")

    tk.Button(
        btn_frame, text="START", command=on_start,
        bg=ACCENT, fg=BG, relief="flat", font=FONT_BOLD,
        padx=28, pady=8, cursor="hand2",
        activebackground="#66E8FF", activeforeground=BG,
    ).pack(side="right")

    root.mainloop()
    return result["start"]
