def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs.setdefault("max_length", 200)
        super().__init__(verbose_name, name, **kwargs)