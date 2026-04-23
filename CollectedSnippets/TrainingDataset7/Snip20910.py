def test_argumented(self):
        class Test:
            @method_decorator(ClsDec(False))
            def method(self):
                return True

        self.assertIs(Test().method(), False)