def test_decorator_does_not_apply_to_class(self):
        with self.assertRaisesMessage(
            TypeError,
            "@deprecate_posargs cannot be applied to a class. (Apply it to the "
            "__init__ method.)",
        ):

            @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
            class NotThisClass:
                pass