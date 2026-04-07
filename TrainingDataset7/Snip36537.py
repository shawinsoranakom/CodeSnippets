def test_repr_bound_method(self):

        class MyLazyGenerator(SimpleLazyObject):
            def __init__(self):
                super().__init__(self._generate)

            def _generate(self):
                return "test-generated-value"

        obj = MyLazyGenerator()
        self.assertEqual(repr(obj), "<MyLazyGenerator: '<bound method _generate>'>")
        self.assertIs(obj._wrapped, empty)  # The evaluation hasn't happened.

        self.assertEqual(str(obj), "test-generated-value")  # Evaluate.
        self.assertEqual(repr(obj), "<MyLazyGenerator: 'test-generated-value'>")