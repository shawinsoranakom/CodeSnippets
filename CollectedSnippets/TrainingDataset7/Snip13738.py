def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fake storage of results to reduce memory usage. These are used by the
        # unittest default methods, but here 'events' is used instead.
        dummy_list = DummyList()
        self.failures = dummy_list
        self.errors = dummy_list
        self.skipped = dummy_list
        self.expectedFailures = dummy_list
        self.unexpectedSuccesses = dummy_list

        if tblib is not None:
            tblib.pickling_support.install()
        self.events = []