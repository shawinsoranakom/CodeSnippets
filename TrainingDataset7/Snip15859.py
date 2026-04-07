def test_command_does_not_import(self):
        """
        startproject doesn't import modules (and cannot be fooled by a module
        raising ImportError).
        """
        bad_name = "raises_import_error"
        args = ["startproject", bad_name]
        testproject_dir = os.path.join(self.test_dir, bad_name)

        with open(os.path.join(self.test_dir, "raises_import_error.py"), "w") as f:
            f.write("raise ImportError")

        out, err = self.run_django_admin(args)
        self.assertOutput(
            err,
            "CommandError: 'raises_import_error' conflicts with the name of an "
            "existing Python module and cannot be used as a project name. Please try "
            "another name.",
        )
        self.assertNoOutput(out)
        self.assertFalse(os.path.exists(testproject_dir))