def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Protect against annotations being passed to __init__ --
        # this'll make the test suite get angry if annotations aren't
        # treated differently than fields.
        for k in kwargs:
            assert k in [f.attname for f in self._meta.fields], (
                "Author.__init__ got an unexpected parameter: %s" % k
            )