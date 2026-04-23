def test_multiple_namespace_pattern(self):
        """Namespaces can be embedded."""
        test_urls = [
            ("inc-ns1:test-ns3:urlobject-view", [], {}, "/ns-included1/test3/inner/"),
            (
                "inc-ns1:test-ns3:urlobject-view",
                [37, 42],
                {},
                "/ns-included1/test3/inner/37/42/",
            ),
            (
                "inc-ns1:test-ns3:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/ns-included1/test3/inner/42/37/",
            ),
            (
                "inc-ns1:test-ns3:urlobject-special-view",
                [],
                {},
                "/ns-included1/test3/inner/+%5C$*/",
            ),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)