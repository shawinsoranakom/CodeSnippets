def test_app_object(self):
        """
        Dynamic URL objects can return a (pattern, app_name) 2-tuple, and
        include() can set the namespace.
        """
        test_urls = [
            ("new-ns1:urlobject-view", [], {}, "/newapp1/inner/"),
            ("new-ns1:urlobject-view", [37, 42], {}, "/newapp1/inner/37/42/"),
            (
                "new-ns1:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/newapp1/inner/42/37/",
            ),
            ("new-ns1:urlobject-special-view", [], {}, "/newapp1/inner/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)