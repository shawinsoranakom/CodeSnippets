def test_check_unique_namespaces(self):
        result = check_url_namespaces_unique(None)
        self.assertEqual(result, [])