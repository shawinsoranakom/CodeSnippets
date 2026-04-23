def test_dirs_not_tuple_or_list(self):
        self.assertEqual(
            check_finders(None),
            [
                Error(
                    "The STATICFILES_DIRS setting is not a tuple or list.",
                    hint="Perhaps you forgot a trailing comma?",
                    id="staticfiles.E001",
                )
            ],
        )