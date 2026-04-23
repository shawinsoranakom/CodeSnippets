def __init__(self, **kwargs):
        if "widget" not in kwargs:
            kwargs["widget"] = RangeWidget(self.base_field.widget)
        if "fields" not in kwargs:
            kwargs["fields"] = [
                self.base_field(required=False),
                self.base_field(required=False),
            ]
        kwargs.setdefault("required", False)
        kwargs.setdefault("require_all_fields", False)
        self.range_kwargs = {}
        if default_bounds := kwargs.pop("default_bounds", None):
            self.range_kwargs = {"bounds": default_bounds}
        super().__init__(**kwargs)