async def test_preserve_signature(self):
        class Test:
            @async_simple_dec_m
            async def say(self, msg):
                return f"Saying {msg}"

        self.assertEqual(await Test().say("hello"), "returned: Saying hello")