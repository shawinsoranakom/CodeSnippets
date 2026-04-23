def __call__(self, result=None):
        """
        Wrapper around default __call__ method to perform common Django test
        set up. This means that user-defined TestCases aren't required to
        include a call to super().setUp().
        """
        self._setup_and_call(result)