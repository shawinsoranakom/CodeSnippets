def test_app_object_default_namespace(self):
        """
        Namespace defaults to app_name when including a (pattern, app_name)
        2-tuple.
        """
        test_urls = [
            ("newapp:urlobject-view", [], {}, "/new-default/inner/"),
            ("newapp:urlobject-view", [37, 42], {}, "/new-default/inner/37/42/"),
            (
                "newapp:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/new-default/inner/42/37/",
            ),
            ("newapp:urlobject-special-view", [], {}, "/new-default/inner/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)