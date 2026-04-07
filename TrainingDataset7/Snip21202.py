def test_decorator_requires_remappable_names_exist(self):
        """remappable_names cannot refer to variable kwargs."""
        with self.assertRaisesMessage(
            TypeError,
            "@deprecate_posargs() requires all remappable_names to be keyword-only "
            "parameters.",
        ):

            @deprecate_posargs(RemovedAfterNextVersionWarning, ["b", "c"])
            def func(a, *, b=1, **kwargs):
                c = kwargs.get("c")
                return a, b, c