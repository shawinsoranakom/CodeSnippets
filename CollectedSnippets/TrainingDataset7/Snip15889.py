def test_custom_app_directory_creation_error_handling(self):
        """The error is displayed to the user in case of OSError."""
        args = [
            "startapp",
            "my_app",
            "project_dir/my_app",
        ]
        # Create a read-only parent directory.
        os.makedirs(
            os.path.join(self.test_dir, "project_dir"), exist_ok=True, mode=0o200
        )
        testapp_dir = os.path.join(self.test_dir, "project_dir", "my_app")
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertOutput(
            err,
            "Permission denied",
        )
        self.assertFalse(os.path.exists(testapp_dir))