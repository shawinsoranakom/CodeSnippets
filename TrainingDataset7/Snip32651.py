def test_add_domain(self):
        """
        add_domain() prefixes domains onto the correct URLs.
        """
        prefix_domain_mapping = (
            (("example.com", "/foo/?arg=value"), "http://example.com/foo/?arg=value"),
            (
                ("example.com", "/foo/?arg=value", True),
                "https://example.com/foo/?arg=value",
            ),
            (
                ("example.com", "http://djangoproject.com/doc/"),
                "http://djangoproject.com/doc/",
            ),
            (
                ("example.com", "https://djangoproject.com/doc/"),
                "https://djangoproject.com/doc/",
            ),
            (
                ("example.com", "mailto:uhoh@djangoproject.com"),
                "mailto:uhoh@djangoproject.com",
            ),
            (
                ("example.com", "//example.com/foo/?arg=value"),
                "http://example.com/foo/?arg=value",
            ),
        )
        for prefix in prefix_domain_mapping:
            with self.subTest(prefix=prefix):
                self.assertEqual(views.add_domain(*prefix[0]), prefix[1])