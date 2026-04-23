def test_include_2_tuple(self):
        self.assertEqual(
            include((self.url_patterns, "app_name")),
            (self.url_patterns, "app_name", "app_name"),
        )