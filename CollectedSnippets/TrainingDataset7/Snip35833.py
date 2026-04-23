def test_current_app_no_partial_match(self):
        """current_app shouldn't be used unless it matches the whole path."""
        test_urls = [
            (
                "inc-ns1:testapp:urlobject-view",
                [],
                {},
                "nonexistent:test-ns3",
                "/ns-included1/test4/inner/",
            ),
            (
                "inc-ns1:testapp:urlobject-view",
                [37, 42],
                {},
                "nonexistent:test-ns3",
                "/ns-included1/test4/inner/37/42/",
            ),
            (
                "inc-ns1:testapp:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "nonexistent:test-ns3",
                "/ns-included1/test4/inner/42/37/",
            ),
            (
                "inc-ns1:testapp:urlobject-special-view",
                [],
                {},
                "nonexistent:test-ns3",
                "/ns-included1/test4/inner/+%5C$*/",
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