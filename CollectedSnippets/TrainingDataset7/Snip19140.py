def test_get_or_set_callable(self):
        def my_callable():
            return "value"

        self.assertEqual(cache.get_or_set("mykey", my_callable), "value")
        self.assertEqual(cache.get_or_set("mykey", my_callable()), "value")

        self.assertIsNone(cache.get_or_set("null", lambda: None))
        # Previous get_or_set() stores None in the cache.
        self.assertIsNone(cache.get("null", "default"))