def _setup_and_call(self, result, debug=False):
        """
        Perform the following in order: pre-setup, run test, post-teardown,
        skipping pre/post hooks if test is set to be skipped.

        If debug=True, reraise any errors in setup and use super().debug()
        instead of __call__() to run the test.
        """
        testMethod = getattr(self, self._testMethodName)
        skipped = getattr(self.__class__, "__unittest_skip__", False) or getattr(
            testMethod, "__unittest_skip__", False
        )

        # Convert async test methods.
        if iscoroutinefunction(testMethod):
            setattr(self, self._testMethodName, async_to_sync(testMethod))

        if not skipped:
            try:
                if self.__class__._pre_setup_ran_eagerly:
                    self.__class__._pre_setup_ran_eagerly = False
                else:
                    self._pre_setup()
            except Exception:
                if debug:
                    raise
                result.addError(self, sys.exc_info())
                return
        if debug:
            super().debug()
        else:
            super().__call__(result)
        if not skipped:
            try:
                self._post_teardown()
            except Exception:
                if debug:
                    raise
                result.addError(self, sys.exc_info())
                return