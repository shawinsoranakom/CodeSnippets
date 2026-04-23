def test_simple_included_name(self):
        """Normal lookups work on names included from other patterns."""
        test_urls = [
            ("included_namespace_urls:inc-normal-view", [], {}, "/included/normal/"),
            (
                "included_namespace_urls:inc-normal-view",
                [37, 42],
                {},
                "/included/normal/37/42/",
            ),
            (
                "included_namespace_urls:inc-normal-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/included/normal/42/37/",
            ),
            ("included_namespace_urls:inc-special-view", [], {}, "/included/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)