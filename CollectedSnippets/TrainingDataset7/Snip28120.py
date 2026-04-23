def test_cache_name_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            FieldCacheMixin().cache_name