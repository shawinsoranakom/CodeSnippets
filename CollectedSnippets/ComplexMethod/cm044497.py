def set(self, value: T) -> None:
        """ Set the item's option value

        Parameters
        ----------
        value : Any
            The value to set this item to. Must be of type :attr:`datatype`

        Raises
        ------
        ValueError
            If the given value does not pass type and content validation checks
        """
        if not self._name:
            raise ValueError("The name of this object should have been set before any value is"
                             "added")

        if self.datatype is list:
            if not isinstance(value, (str, list)):
                raise ValueError(f"[{self._name}] List values should be set as a Str or List. Got "
                                 f"{type(value)} ({value})")
            value = cast(T, self._parse_list(value))

        if not isinstance(value, self.datatype):
            raise ValueError(
                f"[{self._name}] Expected {self.datatype} got {type(value)} ({value})")

        if isinstance(self.choices, list) and self.choices:
            assert isinstance(value, (list, str))
            value = cast(T, self._validate_selection(value))

        if self.choices == "colorchooser":
            assert isinstance(value, str)
            if not value.startswith("#") or len(value) != 7:
                raise ValueError(f"Hex color codes should start with a '#' and be 6 "
                                 f"characters long. Got: '{value}'")

        self._value = value