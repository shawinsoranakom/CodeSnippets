def test_get_cached_value_missing(self):
        with self.assertRaises(KeyError):
            self.field.get_cached_value(self.instance)