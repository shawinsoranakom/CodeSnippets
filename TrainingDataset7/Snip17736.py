def __init__(self, *args, failing_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.failing_fields = failing_fields or {}