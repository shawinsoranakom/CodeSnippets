def test_with_width_only(self):
        """When only width parameter is passed"""
        self._do_test(lambda fn, df: fn(df, width=20), 20, 0)