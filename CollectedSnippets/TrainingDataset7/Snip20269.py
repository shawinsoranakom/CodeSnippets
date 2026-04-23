def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 10
        super().__init__(*args, **kwargs)