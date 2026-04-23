def test_app_lookup_object_with_default(self):
        """A default application namespace is sensitive to the current app."""
        test_urls = [
            ("testapp:urlobject-view", [], {}, "test-ns3", "/default/inner/"),
            (
                "testapp:urlobject-view",
                [37, 42],
                {},
                "test-ns3",
                "/default/inner/37/42/",
            ),
            (
                "testapp:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "test-ns3",
                "/default/inner/42/37/",
            ),
            (
                "testapp:urlobject-special-view",
                [],
                {},
                "test-ns3",
                "/default/inner/+%5C$*/",
            ),
        ]
        for name, args, kwargs, current_app, expected in test_urls:
            with self.subTest(
                name=name, args=args, kwargs=kwargs, current_app=current_app
            ):
                self.assertEqual(
                    reverse(name, args=args, kwargs=kwargs, current_app=current_app),
                    expected,
                )