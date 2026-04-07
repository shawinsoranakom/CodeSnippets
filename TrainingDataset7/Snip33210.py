def test_email(self):
        self.assertEqual(
            urlize("info@djangoproject.org"),
            '<a href="mailto:info@djangoproject.org">info@djangoproject.org</a>',
        )