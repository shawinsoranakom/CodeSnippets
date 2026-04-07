def test_delete_many(self):
        "delete_many does nothing for the dummy cache backend"
        cache.delete_many(["a", "b"])