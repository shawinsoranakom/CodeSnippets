def __init__(self, **kwargs):
        kwargs["max_digits"] = 20
        kwargs["decimal_places"] = 2
        super().__init__(**kwargs)