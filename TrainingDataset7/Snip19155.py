def test_delete_many_num_queries(self):
        cache.set_many({"a": 1, "b": 2, "c": 3})
        with self.assertNumQueries(1):
            cache.delete_many(["a", "b", "c"])