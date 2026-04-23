def update_config(self) -> None:
        """Update :attr:`config` with the currently selected values from the GUI."""
        for section, options in self.tk_vars.items():
            for option_name, tk_option in options.items():
                try:
                    new_value = tk_option.get()
                except tk.TclError as err:
                    # When manually filling in text fields, blank values will
                    # raise an error on numeric data types so return 0
                    logger.trace(  # type:ignore[attr-defined]
                        "Error getting value. Defaulting to 0. Error: %s", str(err))
                    new_value = "" if isinstance(tk_option, tk.StringVar) else 0
                option = self._config.sections[section].options[option_name]
                old_value = option.value
                if new_value == old_value or (isinstance(old_value, list) and
                                              set(str(new_value).split()) == set(old_value)):
                    logger.trace("Skipping unchanged option '%s'",  # type:ignore[attr-defined]
                                 option_name)
                logger.debug("Updating config: '%s', '%s' from %s to %s",
                             section, option_name, repr(old_value), repr(new_value))
                option.set(new_value)