def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache shared by all the get_for_* methods to speed up
        # ContentType retrieval.
        self._cache = {}