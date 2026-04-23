def test_decorator_requires_remappable_names_be_keyword_only(self):
        """remappable_names cannot refer to positional-or-keyword params."""
        with self.assertRaisesMessage(
            TypeError,
            "@deprecate_posargs() requires all remappable_names to be keyword-only "
            "parameters.",
        ):

            @deprecate_posargs(RemovedAfterNextVersionWarning, ["a", "b"])
            def func(a, *, b=1):
                return a, b