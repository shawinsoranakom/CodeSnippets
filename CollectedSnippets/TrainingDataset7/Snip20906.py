def test_preserve_signature(self):
        class Test:
            @simple_dec_m
            def say(self, arg):
                return arg

        self.assertEqual("test:hello", Test().say("hello"))