def __post_init__(self):
        object.__setattr__(self, "args", normalize_json(self.args))
        object.__setattr__(self, "kwargs", normalize_json(self.kwargs))