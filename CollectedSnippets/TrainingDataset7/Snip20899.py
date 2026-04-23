def test_attributes(self):
        """
        Built-in decorators set certain attributes of the wrapped function.
        """
        self.assertEqual(fully_decorated.__name__, "fully_decorated")
        self.assertEqual(fully_decorated.__doc__, "Expected __doc__")
        self.assertEqual(fully_decorated.__dict__["anything"], "Expected __dict__")