def __init__(self, *args, **kwargs):
        kwargs.setdefault("default", Now)
        super().__init__(*args, **kwargs)