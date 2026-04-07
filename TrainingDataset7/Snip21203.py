def test_decorator_preserves_signature_and_metadata(self):

        def original(a, b=1, *, c=2):
            """Docstring."""
            return a, b, c

        decorated = deprecate_posargs(RemovedAfterNextVersionWarning, ["c"])(original)
        self.assertEqual(original.__name__, decorated.__name__)
        self.assertEqual(original.__qualname__, decorated.__qualname__)
        self.assertEqual(original.__doc__, decorated.__doc__)
        self.assertEqual(inspect.signature(original), inspect.signature(decorated))