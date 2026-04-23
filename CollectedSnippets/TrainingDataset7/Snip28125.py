def test_is_cached_false(self):
        result = self.field.is_cached(self.instance)
        self.assertFalse(result)