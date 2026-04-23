def test_decorator_rejects_var_positional_param(self):
        with self.assertRaisesMessage(
            TypeError,
            "@deprecate_posargs() cannot be used with variable positional `*args`.",
        ):

            @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
            def func(*args, b=1):
                return args, b