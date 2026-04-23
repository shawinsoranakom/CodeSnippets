def subTest(self, msg=_subtest_msg_sentinel, **params):
        """Return a context manager that will return the enclosed block
        of code in a subtest identified by the optional message and
        keyword parameters.  A failure in the subtest marks the test
        case as failed but resumes execution at the end of the enclosed
        block, allowing further test code to be executed.
        """
        if self._outcome is None or not self._outcome.result_supports_subtests:
            yield
            return
        parent = self._subtest
        if parent is None:
            params_map = _OrderedChainMap(params)
        else:
            params_map = parent.params.new_child(params)
        self._subtest = _SubTest(self, msg, params_map)
        try:
            with self._outcome.testPartExecutor(self._subtest, subTest=True):
                yield
            if not self._outcome.success:
                result = self._outcome.result
                if result is not None and result.failfast:
                    raise _ShouldStop
            elif self._outcome.expectedFailure:
                # If the test is expecting a failure, we really want to
                # stop now and register the expected failure.
                raise _ShouldStop
        finally:
            self._subtest = parent