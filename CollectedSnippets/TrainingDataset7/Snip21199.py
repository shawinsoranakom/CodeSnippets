def test_decorator_rejects_var_positional_param_with_deferred_annotation(self):
        with self.assertRaisesMessage(
            TypeError,
            "@deprecate_posargs() cannot be used with variable positional `*args`.",
        ):

            @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
            def func(*args, b: AnnotatedKwarg = 1):
                return args, b