def test_preserve_attributes(self):
        async def func(*args, **kwargs):
            await asyncio.sleep(0.01)
            return args, kwargs

        def myattr_dec(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            wrapper.myattr = True
            return wrapper

        def myattr2_dec(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            wrapper.myattr2 = True
            return wrapper

        # Sanity check myattr_dec and myattr2_dec
        func = myattr_dec(func)

        self.assertIs(getattr(func, "myattr", False), True)

        func = myattr2_dec(func)
        self.assertIs(getattr(func, "myattr2", False), True)

        func = myattr_dec(myattr2_dec(func))
        self.assertIs(getattr(func, "myattr", False), True)
        self.assertIs(getattr(func, "myattr2", False), False)

        myattr_dec_m = method_decorator(myattr_dec)
        myattr2_dec_m = method_decorator(myattr2_dec)

        # Decorate using method_decorator() on the async method.
        class TestPlain:
            @myattr_dec_m
            @myattr2_dec_m
            async def method(self):
                "A method"

        # Decorate using method_decorator() on both the class and the method.
        # The decorators applied to the methods are applied before the ones
        # applied to the class.
        @method_decorator(myattr_dec_m, "method")
        class TestMethodAndClass:
            @method_decorator(myattr2_dec_m)
            async def method(self):
                "A method"

        # Decorate using an iterable of function decorators.
        @method_decorator((myattr_dec, myattr2_dec), "method")
        class TestFunctionIterable:
            async def method(self):
                "A method"

        # Decorate using an iterable of method decorators.
        @method_decorator((myattr_dec_m, myattr2_dec_m), "method")
        class TestMethodIterable:
            async def method(self):
                "A method"

        tests = (
            TestPlain,
            TestMethodAndClass,
            TestFunctionIterable,
            TestMethodIterable,
        )
        for Test in tests:
            with self.subTest(Test=Test):
                self.assertIs(getattr(Test().method, "myattr", False), True)
                self.assertIs(getattr(Test().method, "myattr2", False), True)
                self.assertIs(getattr(Test.method, "myattr", False), True)
                self.assertIs(getattr(Test.method, "myattr2", False), True)
                self.assertEqual(Test.method.__doc__, "A method")
                self.assertEqual(Test.method.__name__, "method")