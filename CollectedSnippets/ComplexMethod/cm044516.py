def get_control(self) -> Literal["radio", "multi", "colorchooser", "scale"] | type[
            ttk.Combobox] | type[ttk.Checkbutton] | type[tk.Entry]:
        """ Set the correct control type based on the datatype or for this option """
        control: Literal["radio",
                         "multi",
                         "colorchooser",
                         "scale"] | type[ttk.Combobox] | type[ttk.Checkbutton] | type[tk.Entry]
        if self.choices and self.is_radio:
            control = "radio"
        elif self.choices and self.is_multi_option:
            control = "multi"
        elif self.choices and self.choices == "colorchooser":
            control = "colorchooser"
        elif self.choices:
            control = ttk.Combobox
        elif self.dtype == bool:
            control = ttk.Checkbutton
        elif self.dtype in (int, float):
            control = "scale"
        else:
            control = tk.Entry
        logger.debug("Setting control '%s' to %s", self.title, control)
        return control