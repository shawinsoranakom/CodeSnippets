def test_setup_environ_custom_template(self):
        """
        directory: startapp creates the correct directory with a custom
        template
        """
        template_path = os.path.join(custom_templates_dir, "app_template")
        args = ["startapp", "--template", template_path, "custom_settings_test"]
        app_path = os.path.join(self.test_dir, "custom_settings_test")
        out, err = self.run_django_admin(args, "test_project.settings")
        self.assertNoOutput(err)
        self.assertTrue(os.path.exists(app_path))
        self.assertTrue(os.path.exists(os.path.join(app_path, "api.py")))