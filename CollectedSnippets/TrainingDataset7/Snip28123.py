def test_get_cached_value_default(self):
        default = object()
        result = self.field.get_cached_value(self.instance, default=default)
        self.assertIs(result, default)