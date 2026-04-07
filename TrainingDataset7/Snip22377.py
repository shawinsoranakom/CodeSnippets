def __init__(self, *args, **kwargs):
        kwargs["on_delete"] = models.DO_NOTHING
        super().__init__(*args, **kwargs)