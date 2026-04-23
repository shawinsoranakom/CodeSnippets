def test_trailing_slash_in_target_app_directory_name(self):
        app_dir = os.path.join(self.test_dir, "apps", "app1")
        os.makedirs(app_dir)
        _, err = self.run_django_admin(
            ["startapp", "app", os.path.join("apps", "app1", "")]
        )
        self.assertNoOutput(err)
        self.assertIs(os.path.exists(os.path.join(app_dir, "apps.py")), True)