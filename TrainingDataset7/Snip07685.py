def __init__(self, start, end, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start = start
        self.end = end