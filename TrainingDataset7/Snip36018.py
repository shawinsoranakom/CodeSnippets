def test_is_django_path(self):
        for module, expected in (
            (zoneinfo.__file__, False),
            (contextlib.__file__, False),
            (autoreload.__file__, True),
        ):
            with self.subTest(module=module):
                self.assertIs(autoreload.is_django_path(module), expected)