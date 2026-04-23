def test_setup_environ(self):
        "directory: startapp creates the correct directory"
        args = ["startapp", "settings_test"]
        app_path = os.path.join(self.test_dir, "settings_test")
        out, err = self.run_django_admin(args, "test_project.settings")
        self.assertNoOutput(err)
        self.assertTrue(os.path.exists(app_path))
        with open(os.path.join(app_path, "apps.py")) as f:
            content = f.read()
            self.assertIn("class SettingsTestConfig(AppConfig)", content)
            self.assertInAfterFormatting("name = 'settings_test'", content)