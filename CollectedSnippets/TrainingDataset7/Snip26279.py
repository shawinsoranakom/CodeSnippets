def __init__(self, *args, **kwargs):
                kwargs.setdefault("timeout", 42)
                super().__init__(*args, **kwargs)