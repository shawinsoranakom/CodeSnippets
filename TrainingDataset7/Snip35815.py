def test_non_existent_namespace(self):
        """Nonexistent namespaces raise errors."""
        test_urls = [
            "blahblah:urlobject-view",
            "test-ns1:blahblah:urlobject-view",
        ]
        for name in test_urls:
            with self.subTest(name=name):
                with self.assertRaises(NoReverseMatch):
                    reverse(name)