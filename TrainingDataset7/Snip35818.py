def test_namespace_object(self):
        """Dynamic URL objects can be found using a namespace."""
        test_urls = [
            ("test-ns1:urlobject-view", [], {}, "/test1/inner/"),
            ("test-ns1:urlobject-view", [37, 42], {}, "/test1/inner/37/42/"),
            (
                "test-ns1:urlobject-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/test1/inner/42/37/",
            ),
            ("test-ns1:urlobject-special-view", [], {}, "/test1/inner/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)