def __reduce__(self):
        self.baz = "right"
        return super().__reduce__()