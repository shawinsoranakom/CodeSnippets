def helptext(self) -> str:
        """ str | Description of the config option with additional formating and helptext added
        from the item parameters """
        retval = f"{self.info}\n"
        if not self.fixed:
            retval += _("\nThis option can be updated for existing models.\n")
        if self.datatype == list:
            retval += _("\nIf selecting multiple options then each option should be separated "
                        "by a space or a comma (e.g. item1, item2, item3)\n")
        if self.choices and self.choices != "colorchooser":
            retval += _("\nChoose from: {}").format(self.choices)
        elif self.datatype == bool:
            retval += _("\nChoose from: True, False")
        elif self.datatype == int:
            assert self.min_max is not None
            cmin, cmax = self.min_max
            retval += _("\nSelect an integer between {} and {}").format(cmin, cmax)
        elif self.datatype == float:
            assert self.min_max is not None
            cmin, cmax = self.min_max
            retval += _("\nSelect a decimal number between {} and {}").format(cmin, cmax)
        default = ", ".join(self.default) if isinstance(self.default, list) else self.default
        retval += _("\n[Default: {}]").format(default)
        return retval