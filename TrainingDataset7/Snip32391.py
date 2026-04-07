def test_dirs_contains_static_root(self):
        with self.settings(STATICFILES_DIRS=[settings.STATIC_ROOT]):
            self.assertEqual(
                check_finders(None),
                [
                    Error(
                        "The STATICFILES_DIRS setting should not contain the "
                        "STATIC_ROOT setting.",
                        id="staticfiles.E002",
                    )
                ],
            )