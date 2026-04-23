def test_invalid_name(self):
        """startapp validates that app name is a valid Python identifier."""
        for bad_name in ("7testproject", "../testproject"):
            with self.subTest(app_name=bad_name):
                args = ["startapp", bad_name]
                testproject_dir = os.path.join(self.test_dir, bad_name)

                out, err = self.run_django_admin(args)
                self.assertOutput(
                    err,
                    "CommandError: '{}' is not a valid app name. Please make "
                    "sure the name is a valid identifier.".format(bad_name),
                )
                self.assertFalse(os.path.exists(testproject_dir))