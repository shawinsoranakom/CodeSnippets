def test_app_name_pattern(self):
        """
        Namespaces can be applied to include()'d urlpatterns that set an
        app_name attribute.
        """
        test_urls = [
            ("app-ns1:inc-normal-view", [], {}, "/app-included1/normal/"),
            ("app-ns1:inc-normal-view", [37, 42], {}, "/app-included1/normal/37/42/"),
            (
                "app-ns1:inc-normal-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/app-included1/normal/42/37/",
            ),
            ("app-ns1:inc-special-view", [], {}, "/app-included1/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)