def __init__(self, *, input_date_formats=None, input_time_formats=None, **kwargs):
        errors = self.default_error_messages.copy()
        if "error_messages" in kwargs:
            errors.update(kwargs["error_messages"])
        localize = kwargs.get("localize", False)
        fields = (
            DateField(
                input_formats=input_date_formats,
                error_messages={"invalid": errors["invalid_date"]},
                localize=localize,
            ),
            TimeField(
                input_formats=input_time_formats,
                error_messages={"invalid": errors["invalid_time"]},
                localize=localize,
            ),
        )
        super().__init__(fields, **kwargs)