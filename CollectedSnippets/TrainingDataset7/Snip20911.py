def test_descriptors(self):
        def original_dec(wrapped):
            def _wrapped(arg):
                return wrapped(arg)

            return _wrapped

        method_dec = method_decorator(original_dec)

        class bound_wrapper:
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.__name__ = wrapped.__name__

            def __call__(self, arg):
                return self.wrapped(arg)

            def __get__(self, instance, cls=None):
                return self

        class descriptor_wrapper:
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.__name__ = wrapped.__name__

            def __get__(self, instance, cls=None):
                return bound_wrapper(self.wrapped.__get__(instance, cls))

        class Test:
            @method_dec
            @descriptor_wrapper
            def method(self, arg):
                return arg

        self.assertEqual(Test().method(1), 1)