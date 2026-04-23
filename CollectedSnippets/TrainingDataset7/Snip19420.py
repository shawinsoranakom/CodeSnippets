def test_debug_true(self):
        """
        Warn if DEBUG is True.
        """
        self.assertEqual(base.check_debug(None), [base.W018])