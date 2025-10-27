import tkinter as tk
from tkinter import ttk

def _attach_uppercase_var(widget):
    """
    Ensure the widget has a StringVar textvariable with a trace that forces UPPERCASE.
    Works for tk.Entry / ttk.Entry and ttk.Combobox.
    """
    try:
        # current text (may be '')
        current_text = widget.get() if hasattr(widget, "get") else ""

        var = tk.StringVar(value=str(current_text))

        # Trace callback to force uppercase (safe: only sets when changed)
        def _on_var_change(*_):
            v = var.get()
            u = v.upper()
            if v != u:
                # setting var triggers trace again but the check above prevents loop
                var.set(u)

        # Attach the var to the widget
        widget.config(textvariable=var)
        var.trace("w", _on_var_change)

        # If it's a combobox, also uppercase any current values list
        if isinstance(widget, ttk.Combobox):
            vals = widget.cget("values") or ()
            try:
                uvals = tuple(str(x).upper() for x in vals)
                widget['values'] = uvals
            except Exception:
                pass
    except Exception:
        # be resilient — do not crash UI if something unexpected happens
        pass


class AutocompleteCombobox(ttk.Combobox):
    """
    Combobox with autocomplete + uppercase behavior.
    - Completion list entries are stored/displayed in UPPERCASE.
    - Typed input is converted to UPPERCASE as the user types.
    - Autocomplete/filtering starts after 3 characters.
    """
    def __init__(self, master=None, **kwargs):
        # ensure we have a usable textvariable we can trace
        super().__init__(master, **kwargs)
        self._completion_list = []
        # attach uppercase var to the internal entry part
        _attach_uppercase_var(self)

        # internal state for keyboard navigation
        self.current_index = -1
        self.bind("<Down>", self._select_next)
        self.bind("<Up>", self._select_prev)

        # trace the variable that was just attached
        tv_name = self.cget("textvariable")
        if tv_name:
            # get the actual StringVar object by creating/getting it via widget.nametowidget isn't available;
            # instead rely on get() in callbacks — we already set the widget's textvariable above,
            # and trace on that var will uppercase input. So here we just watch widget's value changes
            # by using the existing trace attached in _attach_uppercase_var.
            pass

        # respond to changes by filtering values (we don't re-attach another trace here to avoid duplication)
        # we'll use <KeyRelease> to trigger filtering
        self.bind("<KeyRelease>", self._on_keyrelease)

    def set_completion_list(self, completion_list):
        """Set and uppercase the completion list and populate values."""
        self._completion_list = [str(x).upper() for x in completion_list if x is not None]
        self['values'] = tuple(self._completion_list)

    def _on_keyrelease(self, event):
        typed = self.get().upper()  # user input is kept uppercase by attached var
        if len(typed) < 3:
            # show full list for <3 chars
            self['values'] = tuple(self._completion_list)
            self.current_index = -1
            return

        matches = [item for item in self._completion_list if item.startswith(typed)]
        self['values'] = tuple(matches if matches else self._completion_list)
        self.current_index = -1

    def _select_next(self, event):
        values = list(self['values']) if self['values'] else []
        if not values:
            return "break"
        self.current_index = (self.current_index + 1) % len(values)
        self.set(values[self.current_index])
        return "break"

    def _select_prev(self, event):
        values = list(self['values']) if self['values'] else []
        if not values:
            return "break"
        self.current_index = (self.current_index - 1) % len(values)
        self.set(values[self.current_index])
        return "break"


class UppercaseEntry(ttk.Entry):
    """
    Entry widget that automatically converts input to uppercase.
    Use this when you explicitly create entry widgets that should always be uppercase.
    """
    def __init__(self, master=None, **kwargs):
        # preserve a textvariable if passed, otherwise create one
        tv = kwargs.pop("textvariable", None)
        if tv is None:
            tv = tk.StringVar()
            kwargs["textvariable"] = tv
        super().__init__(master, **kwargs)

        # attach trace to the provided/created var
        try:
            tv.trace("w", lambda *a: tv.set(tv.get().upper()) if tv.get() != tv.get().upper() else None)
        except Exception:
            # fallback: ensure the widget has a var and a safe trace
            var = tk.StringVar(value=self.get())
            self.config(textvariable=var)
            var.trace("w", lambda *a: var.set(var.get().upper()) if var.get() != var.get().upper() else None)


def add_row(frame, row, col, label_text, widget, label_colspan=1, widget_colspan=1, sticky="w"):
    """
    Place a label and widget in the grid.
    - col is the starting column for the label; widget will be placed at (col + label_colspan).
    - label_colspan / widget_colspan allow spanning.
    - add_row will automatically attach uppercase behavior for Entry / Combobox widgets.
    """
    tk.Label(frame, text=label_text, bg="#E0DDD9").grid(
        row=row, column=col, columnspan=label_colspan, padx=5, pady=5, sticky=sticky
    )

    # attach uppercase enforcement for entries/comboboxes (this makes uppercase "global" for widgets placed with add_row)
    _attach_uppercase_var(widget)

    widget.grid(
        row=row, column=col + label_colspan, columnspan=widget_colspan, padx=5, pady=5, sticky=sticky
    )
