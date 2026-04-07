def test_get_many_num_queries(self):
        cache.set_many({"a": 1, "b": 2})
        cache.set("expired", "expired", 0.01)
        with self.assertNumQueries(1):
            self.assertEqual(cache.get_many(["a", "b"]), {"a": 1, "b": 2})
        time.sleep(0.02)
        with self.assertNumQueries(2):
            self.assertEqual(cache.get_many(["a", "b", "expired"]), {"a": 1, "b": 2})