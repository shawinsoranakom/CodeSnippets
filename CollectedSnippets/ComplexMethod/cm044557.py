def _on_optional_click(self, button):
        """ Click event for all of the optional buttons.

        Parameters
        ----------
        button: str
            The action name for the button that has called this event as exists in :attr:`_buttons`
        """
        options = self._optional_buttons[self._selected_action.get()]
        group = options[button]["group"]
        for child in options["frame"].winfo_children():
            if child.winfo_class() != "TButton":
                continue
            child_group = options[child]["group"]
            if child == button and group is not None:
                child.configure(style="actions_selected.TButton")
                child.state(["pressed", "focus"])
                options[child]["tk_var"].set(True)
            elif child != button and group is not None and child_group == group:
                child.configure(style="actions_deselected.TButton")
                child.state(["!pressed", "!focus"])
                options[child]["tk_var"].set(False)
            elif group is None and child_group is None:
                if child.cget("style") == "actions_selected.TButton":
                    child.configure(style="actions_deselected.TButton")
                    child.state(["!pressed", "!focus"])
                    options[child]["tk_var"].set(False)
                else:
                    child.configure(style="actions_selected.TButton")
                    child.state(["pressed", "focus"])
                    options[child]["tk_var"].set(True)