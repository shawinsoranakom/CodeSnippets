async def test_argumented(self):

        class ClsDecAsync:
            def __init__(self, myattr):
                self.myattr = myattr

            def __call__(self, f):
                async def wrapper():
                    result = await f()
                    return f"{result} appending {self.myattr}"

                return update_wrapper(wrapper, f)

        class Test:
            @method_decorator(ClsDecAsync(False))
            async def method(self):
                return True

        self.assertEqual(await Test().method(), "True appending False")