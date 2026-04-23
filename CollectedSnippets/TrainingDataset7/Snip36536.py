def test_repr(self):
        # First, for an unevaluated SimpleLazyObject
        obj = self.lazy_wrap(42)
        # __repr__ contains __repr__ of setup function and does not evaluate
        # the SimpleLazyObject
        self.assertRegex(repr(obj), "^<SimpleLazyObject:")
        self.assertIs(obj._wrapped, empty)  # make sure evaluation hasn't been triggered

        self.assertEqual(obj, 42)  # evaluate the lazy object
        self.assertIsInstance(obj._wrapped, int)
        self.assertEqual(repr(obj), "<SimpleLazyObject: 42>")