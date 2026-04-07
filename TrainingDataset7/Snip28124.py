def test_get_cached_value_after_set(self):
        value = object()

        self.field.set_cached_value(self.instance, value)
        result = self.field.get_cached_value(self.instance)

        self.assertIs(result, value)