def test_class_methods(self):
        """
        Deprecations for class methods should be bound properly and should
        omit the `self` or `cls` argument from the suggested replacement.
        """

        class SomeClass:
            @deprecate_posargs(RemovedAfterNextVersionWarning, ["a", "b"])
            def __init__(self, *, a=0, b=1):
                self.a = a
                self.b = b

            @deprecate_posargs(RemovedAfterNextVersionWarning, ["a", "b"])
            def some_method(self, *, a, b=1):
                return self.a, self.b, a, b

            @staticmethod
            @deprecate_posargs(RemovedAfterNextVersionWarning, ["a", "b"])
            def some_static_method(*, a, b=1):
                return a, b

            @classmethod
            @deprecate_posargs(RemovedAfterNextVersionWarning, ["a", "b"])
            def some_class_method(cls, *, a, b=1):
                return cls.__name__, a, b

        with (
            self.subTest("Constructor"),
            # Warning should use the class name, not `__init__()`.
            self.assertDeprecated("'a', 'b'", "SomeClass"),
        ):
            instance = SomeClass(10, 20)
            self.assertEqual(instance.a, 10)
            self.assertEqual(instance.b, 20)

        with (
            self.subTest("Instance method"),
            self.assertDeprecated("'a', 'b'", "some_method"),
        ):
            result = SomeClass().some_method(10, 20)
            self.assertEqual(result, (0, 1, 10, 20))

        with (
            self.subTest("Static method on instance"),
            self.assertDeprecated("'a', 'b'", "some_static_method"),
        ):
            result = SomeClass().some_static_method(10, 20)
            self.assertEqual(result, (10, 20))

        with (
            self.subTest("Static method on class"),
            self.assertDeprecated("'a', 'b'", "some_static_method"),
        ):
            result = SomeClass.some_static_method(10, 20)
            self.assertEqual(result, (10, 20))

        with (
            self.subTest("Class method on instance"),
            self.assertDeprecated("'a', 'b'", "some_class_method"),
        ):
            result = SomeClass().some_class_method(10, 20)
            self.assertEqual(result, ("SomeClass", 10, 20))

        with (
            self.subTest("Class method on class"),
            self.assertDeprecated("'a', 'b'", "some_class_method"),
        ):
            result = SomeClass.some_class_method(10, 20)
            self.assertEqual(result, ("SomeClass", 10, 20))