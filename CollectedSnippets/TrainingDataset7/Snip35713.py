def test_path_lookup_with_double_inclusion(self):
        match = resolve("/included_urls/more/some_value/")
        self.assertEqual(match.url_name, "inner-more")
        self.assertEqual(match.route, r"included_urls/more/(?P<extra>\w+)/$")