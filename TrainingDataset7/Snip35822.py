def test_namespace_pattern(self):
        """Namespaces can be applied to include()'d urlpatterns."""
        test_urls = [
            ("inc-ns1:inc-normal-view", [], {}, "/ns-included1/normal/"),
            ("inc-ns1:inc-normal-view", [37, 42], {}, "/ns-included1/normal/37/42/"),
            (
                "inc-ns1:inc-normal-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/ns-included1/normal/42/37/",
            ),
            ("inc-ns1:inc-special-view", [], {}, "/ns-included1/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)