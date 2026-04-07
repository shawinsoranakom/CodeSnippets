async def test_new_attribute(self):
        """A decorator that sets a new attribute on the method."""

        def decorate(func):
            func.x = 1
            return func

        class MyClass:
            @method_decorator(decorate)
            async def method(self):
                return True

        obj = MyClass()
        self.assertEqual(obj.method.x, 1)
        self.assertIs(await obj.method(), True)