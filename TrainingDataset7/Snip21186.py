def test_detects_extra_positional_arguments(self):
        @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
        def func(a, *, b=1):
            return a, b

        with self.assertRaisesMessage(
            TypeError,
            "func() takes at most 2 positional argument(s) (including 1 deprecated) "
            "but 3 were given.",
        ):
            func(10, 20, 30)