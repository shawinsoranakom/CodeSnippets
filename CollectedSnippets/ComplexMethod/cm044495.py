def _validate_choices(self) -> None:
        """ Validate that choices have been used correctly

        Raises
        ------
        ValueError
            If any choices options have not been populated correctly
        """
        if self.choices == "colorchooser":
            if not isinstance(self.default, str):
                raise ValueError(f"Config Item default must be a string when selecting "
                                 f"choice='colorchooser'. Got {type(self.default)}")
            if not self.default.startswith("#") or len(self.default) != 7:
                raise ValueError(f"Hex color codes should start with a '#' and be 6 "
                                 f"characters long. Got: '{self.default}'")
        elif self.choices and isinstance(self.default, str) and self.default not in self.choices:
            raise ValueError(f"Config item default value '{self.default}' must exist in "
                             f"in choices {self.choices}")

        if isinstance(self.choices, list) and self.choices:
            unique_choices = set(x.lower() for x in self.choices)
            if len(unique_choices) != len(self.choices):
                raise ValueError("Config item choices must be a unique list")
            if isinstance(self.default, list):
                defaults = set(x.lower() for x in self.default)
            else:
                assert isinstance(self.default, str), type(self.default)
                defaults = {self.default.lower()}
            if not defaults.issubset(unique_choices):
                raise ValueError(f"Config item default {self.default} must exist in choices "
                                 f"{self.choices}")

        if not self.choices and isinstance(self.default, list):
            raise ValueError("Config item of type list must have choices defined")