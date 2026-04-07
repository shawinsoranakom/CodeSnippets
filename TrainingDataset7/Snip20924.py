async def test_class_decoration(self):
        """
        @method_decorator can be used to decorate a class and its methods.
        """

        @method_decorator(async_simple_dec, name="method")
        class Test:
            async def method(self):
                return False

            async def not_method(self):
                return "a string"

        self.assertEqual(await Test().method(), "returned: False")
        self.assertEqual(await Test().not_method(), "a string")