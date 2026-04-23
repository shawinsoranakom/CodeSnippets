def test_creates_directory_when_custom_app_destination_missing(self):
        args = [
            "startapp",
            "my_app",
            "my_app",
        ]
        testapp_dir = os.path.join(self.test_dir, "my_app")
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertNoOutput(err)
        self.assertTrue(os.path.exists(testapp_dir))