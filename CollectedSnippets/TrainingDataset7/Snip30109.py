def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iterable_class = ModelIterableSubclass