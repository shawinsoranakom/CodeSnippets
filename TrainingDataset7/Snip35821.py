def test_embedded_namespace_object(self):
        """Namespaces can be installed anywhere in the URL pattern tree."""
        test_urls = [
            (
                "included_namespace_urls:test-ns3:urlobject-view",
                [],
                {},
                "/included/test3/inner/",
            ),
            (
                "included_namespace_urls:test-ns3:urlobject-view",
                [37, 42],
                {},
                "/included/test3/inner/37/42/",
            ),
            (
                "included_namespace_urls:test-ns3:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/included/test3/inner/42/37/",
            ),
            (
                "included_namespace_urls:test-ns3:urlobject-special-view",
                [],
                {},
                "/included/test3/inner/+%5C$*/",
            ),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)