def test_namespaces_with_variables(self):
        """Namespace prefixes can capture variables."""
        test_urls = [
            ("inc-ns5:inner-nothing", [], {"outer": "70"}, "/inc70/"),
            (
                "inc-ns5:inner-extra",
                [],
                {"extra": "foobar", "outer": "78"},
                "/inc78/extra/foobar/",
            ),
            ("inc-ns5:inner-nothing", ["70"], {}, "/inc70/"),
            ("inc-ns5:inner-extra", ["78", "foobar"], {}, "/inc78/extra/foobar/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(reverse(name, args=args, kwargs=kwargs), expected)