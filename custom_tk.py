import tkinter as tk
from tkinter import simpledialog, messagebox

class CustomAskStringDialog(simpledialog._QueryString):
    def __init__(self, title, prompt, parent, invalid_keys=None, **kwargs):
        self.invalid_keys = invalid_keys or []  # List of invalid keys
        super().__init__(title, prompt, parent, **kwargs)

    def body(self, master):
        """Override the body method to add validation."""
        self.entry_label = tk.Label(master, text=self.prompt, justify="left")
        self.entry_label.grid(row=0, column=0, sticky="w")
        self.entry = tk.Entry(master)
        self.entry.grid(row=1, column=0, padx=5, pady=5, sticky="we")
        self.entry.bind("<KeyRelease>", self.validate_input)  # Bind validation
        return self.entry

    def validate_input(self, event=None):
        """Prevent invalid keys from being entered."""
        value = self.entry.get()
        for key in self.invalid_keys:
            if key in value:
                self.entry.delete(0, tk.END)  # Clear the entry
                self.entry.insert(0, value.replace(key, ""))  # Remove invalid character
                messagebox.showwarning("Invalid Input", f"'{key}' is not allowed.")  # Show warning
                break

def custom_askstring(title, prompt, parent, invalid_keys=None,**kwargs):
    dialog = CustomAskStringDialog(title, prompt, parent, invalid_keys, **kwargs)
    return dialog.result
