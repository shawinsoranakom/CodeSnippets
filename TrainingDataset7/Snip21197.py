def test_decorator_requires_keyword_only_params(self):
        with self.assertRaisesMessage(
            TypeError,
            "@deprecate_posargs() requires at least one keyword-only parameter "
            "(after a `*` entry in the parameters list).",
        ):

            @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
            def func(a, b=1):
                return a, b