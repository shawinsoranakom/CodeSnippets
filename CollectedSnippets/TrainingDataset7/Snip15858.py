def test_importable_project_name(self):
        """
        startproject validates that project name doesn't clash with existing
        Python modules.
        """
        bad_name = "os"
        args = ["startproject", bad_name]
        testproject_dir = os.path.join(self.test_dir, bad_name)

        out, err = self.run_django_admin(args)
        self.assertOutput(
            err,
            "CommandError: 'os' conflicts with the name of an existing "
            "Python module and cannot be used as a project name. Please try "
            "another name.",
        )
        self.assertFalse(os.path.exists(testproject_dir))