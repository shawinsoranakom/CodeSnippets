def __init__(self, *, coerce=lambda val: val, **kwargs):
        self.coerce = coerce
        self.empty_value = kwargs.pop("empty_value", [])
        super().__init__(**kwargs)