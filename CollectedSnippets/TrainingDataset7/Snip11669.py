def __init__(self, expression, lookup_name=None, tzinfo=None, **extra):
        if self.lookup_name is None:
            self.lookup_name = lookup_name
        if self.lookup_name is None:
            raise ValueError("lookup_name must be provided")
        self.tzinfo = tzinfo
        super().__init__(expression, **extra)