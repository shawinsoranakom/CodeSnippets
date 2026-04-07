def __init__(
        self,
        attrs=None,
        date_format=None,
        time_format=None,
        date_attrs=None,
        time_attrs=None,
    ):
        super().__init__(attrs, date_format, time_format, date_attrs, time_attrs)
        for widget in self.widgets:
            widget.input_type = "hidden"