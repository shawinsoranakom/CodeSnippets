def test_app_lookup_object(self):
        """A default application namespace can be used for lookup."""
        test_urls = [
            ("testapp:urlobject-view", [], {}, "/default/inner/"),
            ("testapp:urlobject-view", [37, 42], {}, "/default/inner/37/42/"),
            (
                "testapp:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/default/inner/42/37/",
            ),
            ("testapp:urlobject-special-view", [], {}, "/default/inner/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)