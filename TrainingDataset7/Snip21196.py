def test_warning_source_location(self):
        """The warning points to caller, not the decorator implementation."""

        @deprecate_posargs(RemovedAfterNextVersionWarning, "a")
        def some_func(*, a):
            return a

        with self.assertWarns(RemovedAfterNextVersionWarning) as cm:
            some_func(10)
        self.assertEqual(cm.filename, __file__)
        self.assertEqual(cm.lineno, inspect.currentframe().f_lineno - 2)