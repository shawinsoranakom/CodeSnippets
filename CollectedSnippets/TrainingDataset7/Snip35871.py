def test_include_2_tuple_namespace(self):
        self.assertEqual(
            include((self.url_patterns, "app_name"), namespace="namespace"),
            (self.url_patterns, "app_name", "namespace"),
        )