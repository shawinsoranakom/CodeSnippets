def test_incorrect_staticmethod_order(self):
        """Catch staticmethod applied in wrong order."""
        with self.assertRaisesMessage(
            TypeError, "Apply @staticmethod before @deprecate_posargs."
        ):

            class SomeClass:
                @deprecate_posargs(RemovedAfterNextVersionWarning, ["a"])
                @staticmethod
                def some_static_method(*, a):
                    pass