def test_is_cached_true(self):
        self.field.set_cached_value(self.instance, 1)
        result = self.field.is_cached(self.instance)
        self.assertTrue(result)