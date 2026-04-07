def __init__(self, *, input_formats=None, **kwargs):
        super().__init__(**kwargs)
        if input_formats is not None:
            self.input_formats = input_formats