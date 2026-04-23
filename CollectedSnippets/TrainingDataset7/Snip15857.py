def test_invalid_project_name(self):
        """
        Make sure the startproject management command validates a project name
        """
        for bad_name in ("7testproject", "../testproject"):
            with self.subTest(project_name=bad_name):
                args = ["startproject", bad_name]
                testproject_dir = os.path.join(self.test_dir, bad_name)

                out, err = self.run_django_admin(args)
                self.assertOutput(
                    err,
                    "Error: '%s' is not a valid project name. Please make "
                    "sure the name is a valid identifier." % bad_name,
                )
                self.assertFalse(os.path.exists(testproject_dir))