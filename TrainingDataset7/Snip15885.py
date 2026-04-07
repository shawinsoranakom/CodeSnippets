def test_template(self):
        out, err = self.run_django_admin(["startapp", "new_app"])
        self.assertNoOutput(err)
        app_path = os.path.join(self.test_dir, "new_app")
        self.assertIs(os.path.exists(app_path), True)
        with open(os.path.join(app_path, "apps.py")) as f:
            content = f.read()
            self.assertIn("class NewAppConfig(AppConfig)", content)
            self.assertInAfterFormatting("name = 'new_app'", content)