async def test_tuple_of_decorators(self):
        """
        @method_decorator can accept a tuple of decorators.
        """

        def add_question_mark(func):
            async def _wrapper(*args, **kwargs):
                await asyncio.sleep(0.01)
                return await func(*args, **kwargs) + "?"

            return _wrapper

        def add_exclamation_mark(func):
            async def _wrapper(*args, **kwargs):
                await asyncio.sleep(0.01)
                return await func(*args, **kwargs) + "!"

            return _wrapper

        decorators = (add_exclamation_mark, add_question_mark)

        @method_decorator(decorators, name="method")
        class TestFirst:
            async def method(self):
                return "hello world"

        class TestSecond:
            @method_decorator(decorators)
            async def method(self):
                return "world hello"

        self.assertEqual(await TestFirst().method(), "hello world?!")
        self.assertEqual(await TestSecond().method(), "world hello?!")