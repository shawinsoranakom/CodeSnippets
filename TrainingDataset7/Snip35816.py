def test_normal_name(self):
        """Normal lookups work as expected."""
        test_urls = [
            ("normal-view", [], {}, "/normal/"),
            ("normal-view", [37, 42], {}, "/normal/37/42/"),
            ("normal-view", [], {"arg1": 42, "arg2": 37}, "/normal/42/37/"),
            ("special-view", [], {}, "/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)