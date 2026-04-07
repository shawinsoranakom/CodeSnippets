async def test_descriptors(self):
        class bound_wrapper:
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.__name__ = wrapped.__name__

            async def __call__(self, *args, **kwargs):
                return await self.wrapped(*args, **kwargs)

            def __get__(self, instance, cls=None):
                return self

        class descriptor_wrapper:
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.__name__ = wrapped.__name__

            def __get__(self, instance, cls=None):
                return bound_wrapper(self.wrapped.__get__(instance, cls))

        class Test:
            @async_simple_dec_m
            @descriptor_wrapper
            async def method(self, arg):
                return arg

        self.assertEqual(await Test().method(1), "returned: 1")