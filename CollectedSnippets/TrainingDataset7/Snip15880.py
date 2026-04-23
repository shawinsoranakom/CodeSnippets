def test_importable_name(self):
        """
        startapp validates that app name doesn't clash with existing Python
        modules.
        """
        bad_name = "os"
        args = ["startapp", bad_name]
        testproject_dir = os.path.join(self.test_dir, bad_name)

        out, err = self.run_django_admin(args)
        self.assertOutput(
            err,
            "CommandError: 'os' conflicts with the name of an existing "
            "Python module and cannot be used as an app name. Please try "
            "another name.",
        )
        self.assertFalse(os.path.exists(testproject_dir))