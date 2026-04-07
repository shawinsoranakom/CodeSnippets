def test_app_lookup_object_without_default(self):
        """
        An application namespace without a default is sensitive to the current
        app.
        """
        test_urls = [
            ("nodefault:urlobject-view", [], {}, None, "/other2/inner/"),
            ("nodefault:urlobject-view", [37, 42], {}, None, "/other2/inner/37/42/"),
            (
                "nodefault:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                None,
                "/other2/inner/42/37/",
            ),
            ("nodefault:urlobject-special-view", [], {}, None, "/other2/inner/+%5C$*/"),
            ("nodefault:urlobject-view", [], {}, "other-ns1", "/other1/inner/"),
            (
                "nodefault:urlobject-view",
                [37, 42],
                {},
                "other-ns1",
                "/other1/inner/37/42/",
            ),
            (
                "nodefault:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "other-ns1",
                "/other1/inner/42/37/",
            ),
            (
                "nodefault:urlobject-special-view",
                [],
                {},
                "other-ns1",
                "/other1/inner/+%5C$*/",
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