def __init__(self, *, choices=(), **kwargs):
        super().__init__(**kwargs)
        self.choices = choices