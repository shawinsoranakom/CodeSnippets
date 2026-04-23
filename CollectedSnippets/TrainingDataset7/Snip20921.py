def test_bad_iterable(self):
        decorators = {async_simple_dec}
        msg = "'set' object is not subscriptable"
        with self.assertRaisesMessage(TypeError, msg):

            @method_decorator(decorators, "method")
            class TestIterable:
                async def method(self):
                    await asyncio.sleep(0.01)