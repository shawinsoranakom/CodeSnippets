def test_duplicate_key(self):
        """Two components with the same `key` should throw DuplicateWidgetID exception"""
        self.test_component(foo="bar", key="baz")

        with self.assertRaises(DuplicateWidgetID):
            self.test_component(key="baz")