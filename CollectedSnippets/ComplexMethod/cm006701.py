def __init__(
        self,
        data: list[dict] | list[Data] | pd.DataFrame | None = None,
        text_key: str = "text",
        default_value: str = "",
        **kwargs,
    ):
        # Initialize pandas DataFrame first without data
        super().__init__(**kwargs)  # Removed data parameter

        # Store attributes as private members to avoid conflicts with pandas
        self._text_key = text_key
        self._default_value = default_value

        if data is None:
            return

        if isinstance(data, list):
            if all(isinstance(x, Data) for x in data):
                data = [d.data for d in data if hasattr(d, "data")]
            elif not all(isinstance(x, dict) for x in data):
                msg = "List items must be either all Data objects or all dictionaries"
                raise ValueError(msg)
            self._update(data, **kwargs)
        elif isinstance(data, dict | pd.DataFrame):  # Fixed type check syntax
            self._update(data, **kwargs)