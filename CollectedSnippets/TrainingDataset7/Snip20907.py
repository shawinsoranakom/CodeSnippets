def test_preserve_attributes(self):
        # Sanity check myattr_dec and myattr2_dec
        @myattr_dec
        def func():
            pass

        self.assertIs(getattr(func, "myattr", False), True)

        @myattr2_dec
        def func():
            pass

        self.assertIs(getattr(func, "myattr2", False), True)

        @myattr_dec
        @myattr2_dec
        def func():
            pass

        self.assertIs(getattr(func, "myattr", False), True)
        self.assertIs(getattr(func, "myattr2", False), False)

        # Decorate using method_decorator() on the method.
        class TestPlain:
            @myattr_dec_m
            @myattr2_dec_m
            def method(self):
                "A method"
                pass

        # Decorate using method_decorator() on both the class and the method.
        # The decorators applied to the methods are applied before the ones
        # applied to the class.
        @method_decorator(myattr_dec_m, "method")
        class TestMethodAndClass:
            @method_decorator(myattr2_dec_m)
            def method(self):
                "A method"
                pass

        # Decorate using an iterable of function decorators.
        @method_decorator((myattr_dec, myattr2_dec), "method")
        class TestFunctionIterable:
            def method(self):
                "A method"
                pass

        # Decorate using an iterable of method decorators.
        decorators = (myattr_dec_m, myattr2_dec_m)

        @method_decorator(decorators, "method")
        class TestMethodIterable:
            def method(self):
                "A method"
                pass

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