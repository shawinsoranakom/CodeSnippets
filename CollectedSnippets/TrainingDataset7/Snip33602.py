def test_filter_syntax25(self):
        """
        #16383 - Attribute errors from an @property value should be
        reraised.
        """
        with self.assertRaises(AttributeError):
            self.engine.render_to_string("filter-syntax25", {"var": SomeClass()})