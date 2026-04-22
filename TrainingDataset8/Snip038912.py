def test_no_dimensions(self):
        """When no dimension parameters are passed"""
        self._do_test(lambda fn, df: fn(df), 0, 0)