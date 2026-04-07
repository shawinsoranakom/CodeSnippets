def test_namespace_pattern_with_variable_prefix(self):
        """
        Using include() with namespaces when there is a regex variable in front
        of it.
        """
        test_urls = [
            ("inc-outer:inc-normal-view", [], {"outer": 42}, "/ns-outer/42/normal/"),
            ("inc-outer:inc-normal-view", [42], {}, "/ns-outer/42/normal/"),
            (
                "inc-outer:inc-normal-view",
                [],
                {"arg1": 37, "arg2": 4, "outer": 42},
                "/ns-outer/42/normal/37/4/",
            ),
            ("inc-outer:inc-normal-view", [42, 37, 4], {}, "/ns-outer/42/normal/37/4/"),
            ("inc-outer:inc-special-view", [], {"outer": 42}, "/ns-outer/42/+%5C$*/"),
            ("inc-outer:inc-special-view", [42], {}, "/ns-outer/42/+%5C$*/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)