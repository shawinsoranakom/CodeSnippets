def test_invalid_target_name(self):
        for bad_target in (
            "invalid.dir_name",
            "7invalid_dir_name",
            ".invalid_dir_name",
        ):
            with self.subTest(bad_target):
                _, err = self.run_django_admin(["startapp", "app", bad_target])
                self.assertOutput(
                    err,
                    "CommandError: '%s' is not a valid app directory. Please "
                    "make sure the directory is a valid identifier." % bad_target,
                )