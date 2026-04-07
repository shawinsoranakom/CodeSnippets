def test_incorrect_classmethod_order(self):
        """Catch classmethod applied in wrong order."""
        with self.assertRaisesMessage(
            TypeError, "Apply @classmethod before @deprecate_posargs."
        ):

            class SomeClass:
                @deprecate_posargs(RemovedAfterNextVersionWarning, ["a"])
                @classmethod
                def some_class_method(cls, *, a):
                    pass