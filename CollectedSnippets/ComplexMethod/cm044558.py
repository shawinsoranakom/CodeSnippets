def _display_optional_buttons(self, *args):  # pylint:disable=unused-argument
        """ Pack or forget the optional buttons depending on active editor """
        self._unbind_optional_hotkeys()
        for editor, option in self._optional_buttons.items():
            if option is None:
                continue
            if editor == self._selected_action.get():
                logger.debug("Displaying optional buttons for '%s'", editor)
                option["frame"].pack(side=tk.TOP, fill=tk.Y)
                for child in option["frame"].winfo_children():
                    if child.winfo_class() != "TButton":
                        continue
                    hotkey = option[child]["hotkey"]
                    if hotkey is not None:
                        logger.debug("Binding optional hotkey for editor '%s': %s", editor, hotkey)
                        self.winfo_toplevel().bind(hotkey.lower(),
                                                   lambda e, b=child: self._on_optional_click(b))
            elif option["frame"].winfo_ismapped():
                logger.debug("Hiding optional buttons for '%s'", editor)
                option["frame"].pack_forget()