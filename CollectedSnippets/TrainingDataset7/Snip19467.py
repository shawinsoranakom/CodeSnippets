def test_check_resolver_recursive(self):
        # The resolver is checked recursively (examining URL patterns in
        # include()).
        result = check_url_config(None)
        self.assertEqual(len(result), 1)
        warning = result[0]
        self.assertEqual(warning.id, "urls.W001")