def test_with_height_only(self):
        """When only height parameter is passed"""
        self._do_test(lambda fn, df: fn(df, height=20), 0, 20)