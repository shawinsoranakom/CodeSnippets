def test_with_dimensions(self):
        """When dimension parameter are passed"""
        self._do_test(lambda fn, df: fn(df, 10, 20), 10, 20)