def __init__(self, base_field, size, *, remove_trailing_nulls=False, **kwargs):
        self.base_field = base_field
        self.size = size
        self.remove_trailing_nulls = remove_trailing_nulls
        widget = SplitArrayWidget(widget=base_field.widget, size=size)
        kwargs.setdefault("widget", widget)
        super().__init__(**kwargs)