def test_cache_name(self):
        result = Example().cache_name
        self.assertEqual(result, "example")