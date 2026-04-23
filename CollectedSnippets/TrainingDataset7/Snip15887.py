def test_custom_app_destination_missing_with_nested_subdirectory(self):
        args = [
            "startapp",
            "my_app",
            "apps/my_app",
        ]
        testapp_dir = os.path.join(self.test_dir, "apps", "my_app")
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertNoOutput(err)
        self.assertTrue(os.path.exists(testapp_dir))