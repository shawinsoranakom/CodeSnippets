def __init__(self, *args, **kwargs):
        kwargs["null"] = True
        kwargs["blank"] = True
        super().__init__(*args, **kwargs)