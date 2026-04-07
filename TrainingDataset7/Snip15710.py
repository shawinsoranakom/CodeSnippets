def test_startapp_unicode_name(self):
        """startapp creates the correct directory with Unicode characters."""
        args = ["startapp", "こんにちは"]
        app_path = os.path.join(self.test_dir, "こんにちは")
        out, err = self.run_django_admin(args, "test_project.settings")
        self.assertNoOutput(err)
        self.assertTrue(os.path.exists(app_path))
        with open(os.path.join(app_path, "apps.py"), encoding="utf8") as f:
            content = f.read()
            self.assertIn("class こんにちはConfig(AppConfig)", content)
            self.assertInAfterFormatting("name = 'こんにちは'", content)