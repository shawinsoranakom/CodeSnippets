def test_func_accepts_kwargs_deferred_annotations(self):

        def func_with_annotations(self, name: str, complex: SafeString) -> None:
            pass

        # Inspection fails with deferred annotations with python 3.14+. Earlier
        # Python versions trigger the NameError on module initialization.
        self.assertIs(inspect.func_accepts_kwargs(func_with_annotations), False)