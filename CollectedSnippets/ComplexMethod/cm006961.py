def _validate_input(self) -> None:
        """Validate the input data and raise ValueError if invalid."""
        if self.input_value is None:
            msg = "Input data cannot be None"
            raise ValueError(msg)
        if isinstance(self.input_value, list) and not all(
            isinstance(item, Message | Data | DataFrame | str) for item in self.input_value
        ):
            invalid_types = [
                type(item).__name__
                for item in self.input_value
                if not isinstance(item, Message | Data | DataFrame | str)
            ]
            msg = f"Expected Data or DataFrame or Message or str, got {invalid_types}"
            raise TypeError(msg)
        if not isinstance(
            self.input_value,
            Message | Data | DataFrame | str | list | Generator | type(None),
        ):
            type_name = type(self.input_value).__name__
            msg = f"Expected Data or DataFrame or Message or str, Generator or None, got {type_name}"
            raise TypeError(msg)