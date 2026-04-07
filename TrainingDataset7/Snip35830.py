def test_special_chars_namespace(self):
        test_urls = [
            (
                "special:included_namespace_urls:inc-normal-view",
                [],
                {},
                "/+%5C$*/included/normal/",
            ),
            (
                "special:included_namespace_urls:inc-normal-view",
                [37, 42],
                {},
                "/+%5C$*/included/normal/37/42/",
            ),
            (
                "special:included_namespace_urls:inc-normal-view",
                [],
                {"arg1": 42, "arg2": 37},
                "/+%5C$*/included/normal/42/37/",
            ),
            (
                "special:included_namespace_urls:inc-special-view",
                [],
                {},
                "/+%5C$*/included/+%5C$*/",
            ),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)