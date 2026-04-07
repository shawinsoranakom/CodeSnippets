def test_get_or_set_callable(self):
        def my_callable():
            return "default"

        self.assertEqual(cache.get_or_set("mykey", my_callable), "default")
        self.assertEqual(cache.get_or_set("mykey", my_callable()), "default")