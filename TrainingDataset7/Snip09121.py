def __init__(self, schemes=None, **kwargs):
        super().__init__(**kwargs)
        if schemes is not None:
            self.schemes = schemes