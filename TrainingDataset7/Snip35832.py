def test_nested_app_lookup(self):
        """
        A nested current_app should be split in individual namespaces (#24904).
        """
        test_urls = [
            (
                "inc-ns1:testapp:urlobject-view",
                [],
                {},
                None,
                "/ns-included1/test4/inner/",
            ),
            (
                "inc-ns1:testapp:urlobject-view",
                [37, 42],
                {},
                None,
                "/ns-included1/test4/inner/37/42/",
            ),
            (
                "inc-ns1:testapp:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                None,
                "/ns-included1/test4/inner/42/37/",
            ),
            (
                "inc-ns1:testapp:urlobject-special-view",
                [],
                {},
                None,
                "/ns-included1/test4/inner/+%5C$*/",
            ),
            (
                "inc-ns1:testapp:urlobject-view",
                [],
                {},
                "inc-ns1:test-ns3",
                "/ns-included1/test3/inner/",
            ),
            (
                "inc-ns1:testapp:urlobject-view",
                [37, 42],
                {},
                "inc-ns1:test-ns3",
                "/ns-included1/test3/inner/37/42/",
            ),
            (
                "inc-ns1:testapp:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "inc-ns1:test-ns3",
                "/ns-included1/test3/inner/42/37/",
            ),
            (
                "inc-ns1:testapp:urlobject-special-view",
                [],
                {},
                "inc-ns1:test-ns3",
                "/ns-included1/test3/inner/+%5C$*/",
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