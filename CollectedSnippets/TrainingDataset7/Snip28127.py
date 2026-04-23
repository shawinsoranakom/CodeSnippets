def test_delete_cached_value(self):
        self.field.set_cached_value(self.instance, 1)
        self.field.delete_cached_value(self.instance)
        result = self.field.is_cached(self.instance)
        self.assertFalse(result)