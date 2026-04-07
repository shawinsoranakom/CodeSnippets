def test_same_instance(self):
        cache1 = storages["custom_storage"]
        cache2 = storages["custom_storage"]
        self.assertIs(cache1, cache2)