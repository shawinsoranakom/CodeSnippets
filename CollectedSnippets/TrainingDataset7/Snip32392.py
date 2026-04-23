def test_dirs_contains_static_root_in_tuple(self):
        with self.settings(STATICFILES_DIRS=[("prefix", settings.STATIC_ROOT)]):
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