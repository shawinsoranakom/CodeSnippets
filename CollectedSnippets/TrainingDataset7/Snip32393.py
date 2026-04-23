def test_prefix_contains_trailing_slash(self):
        static_dir = Path(TEST_ROOT) / "project" / "documents"
        with self.settings(STATICFILES_DIRS=[("prefix/", static_dir)]):
            self.assertEqual(
                check_finders(None),
                [
                    Error(
                        "The prefix 'prefix/' in the STATICFILES_DIRS setting must "
                        "not end with a slash.",
                        id="staticfiles.E003",
                    ),
                ],
            )