def __init__(self, *args, default_bounds=CANONICAL_RANGE_BOUNDS, **kwargs):
        if default_bounds not in ("[)", "(]", "()", "[]"):
            raise ValueError("default_bounds must be one of '[)', '(]', '()', or '[]'.")
        self.default_bounds = default_bounds
        super().__init__(*args, **kwargs)