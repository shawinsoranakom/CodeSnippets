def test_check_non_unique_namespaces(self):
        result = check_url_namespaces_unique(None)
        self.assertEqual(len(result), 2)
        non_unique_namespaces = ["app-ns1", "app-1"]
        warning_messages = [
            "URL namespace '{}' isn't unique. You may not be able to reverse "
            "all URLs in this namespace".format(namespace)
            for namespace in non_unique_namespaces
        ]
        for warning in result:
            self.assertIsInstance(warning, Warning)
            self.assertEqual("urls.W005", warning.id)
            self.assertIn(warning.msg, warning_messages)