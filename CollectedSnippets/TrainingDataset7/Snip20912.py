def test_class_decoration(self):
        """
        @method_decorator can be used to decorate a class and its methods.
        """

        def deco(func):
            def _wrapper(*args, **kwargs):
                return True

            return _wrapper

        @method_decorator(deco, name="method")
        class Test:
            def method(self):
                return False

        self.assertTrue(Test().method())