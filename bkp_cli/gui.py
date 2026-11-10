"""GUI: Tkinter window for editing settings."""

import tkinter as tk
from tkinter import filedialog, ttk

from bkp_cli.settings import Settings, save_settings


def open_settings_window(current_settings: Settings, settings_path: str = "settings.json") -> None:
    """Open a modal Tkinter window for editing settings.

    Blocks until the window is closed. Writes to settings_path only if
    the user clicks Save; Cancel (or closing the window) discards all
    in-memory edits.
    """
    state = {
        "source": current_settings.source,
        "target": current_settings.target,
        "whitelist": list(current_settings.whitelist),
    }

    root = tk.Tk()
    root.title("bkp-cli - config set")
    root.resizable(False, False)

    source_var = tk.StringVar(value=state["source"])
    target_var = tk.StringVar(value=state["target"])

    def browse_source():
        chosen = filedialog.askdirectory(title="Select source directory")
        if chosen:
            state["source"] = chosen
            source_var.set(chosen)

    def browse_target():
        chosen = filedialog.askdirectory(title="Select target directory")
        if chosen:
            state["target"] = chosen
            target_var.set(chosen)

    # Source row
    source_frame = ttk.Frame(root, padding=(10, 10, 10, 5))
    source_frame.grid(row=0, column=0, sticky="ew")
    ttk.Label(source_frame, text="Source:").grid(row=0, column=0, sticky="w")
    ttk.Entry(source_frame, textvariable=source_var, width=50, state="readonly").grid(
        row=0, column=1, padx=5
    )
    ttk.Button(source_frame, text="Browse...", command=browse_source).grid(row=0, column=2)

    # Target row
    target_frame = ttk.Frame(root, padding=(10, 5, 10, 5))
    target_frame.grid(row=1, column=0, sticky="ew")
    ttk.Label(target_frame, text="Target:").grid(row=0, column=0, sticky="w")
    ttk.Entry(target_frame, textvariable=target_var, width=50, state="readonly").grid(
        row=0, column=1, padx=5
    )
    ttk.Button(target_frame, text="Browse...", command=browse_target).grid(row=0, column=2)

    # Whitelist section
    whitelist_frame = ttk.LabelFrame(root, text="Whitelist", padding=(10, 5, 10, 5))
    whitelist_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

    list_container = ttk.Frame(whitelist_frame)
    list_container.grid(row=0, column=0, sticky="ew")

    canvas = tk.Canvas(list_container, height=120, width=430, highlightthickness=0)
    scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
    rows_frame = ttk.Frame(canvas)

    rows_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=rows_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.grid(row=0, column=0, sticky="ew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    def refresh_whitelist_rows():
        for widget in rows_frame.winfo_children():
            widget.destroy()

        if not state["whitelist"]:
            ttk.Label(rows_frame, text="(empty)").grid(row=0, column=0, sticky="w")
            return

        for index, entry in enumerate(state["whitelist"]):
            ttk.Label(rows_frame, text=entry, width=55, anchor="w").grid(
                row=index, column=0, sticky="w"
            )
            ttk.Button(
                rows_frame,
                text="Remove",
                command=lambda e=entry: remove_whitelist_entry(e),
            ).grid(row=index, column=1, padx=5)

    def remove_whitelist_entry(entry: str):
        if entry in state["whitelist"]:
            state["whitelist"].remove(entry)
        refresh_whitelist_rows()

    def add_whitelist_entry():
        chosen = filedialog.askdirectory(title="Select directory to whitelist")
        if chosen and chosen not in state["whitelist"]:
            state["whitelist"].append(chosen)
        refresh_whitelist_rows()

    refresh_whitelist_rows()

    ttk.Button(whitelist_frame, text="Add...", command=add_whitelist_entry).grid(
        row=1, column=0, sticky="w", pady=(5, 0)
    )

    # Save / Cancel buttons
    def on_save():
        new_settings = Settings(
            source=state["source"],
            target=state["target"],
            whitelist=list(state["whitelist"]),
        )
        save_settings(new_settings, settings_path)
        root.destroy()

    def on_cancel():
        root.destroy()

    button_frame = ttk.Frame(root, padding=(10, 5, 10, 10))
    button_frame.grid(row=3, column=0, sticky="e")
    ttk.Button(button_frame, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=5)
    ttk.Button(button_frame, text="Save", command=on_save).grid(row=0, column=1)

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()
