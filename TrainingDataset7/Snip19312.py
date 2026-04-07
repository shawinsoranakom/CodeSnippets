async def test_aget_or_set_callable(self):
        def my_callable():
            return "default"

        self.assertEqual(await cache.aget_or_set("key", my_callable), "default")
        self.assertEqual(await cache.aget_or_set("key", my_callable()), "default")