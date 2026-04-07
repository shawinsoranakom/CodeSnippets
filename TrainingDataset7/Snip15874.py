def test_custom_project_template_hidden_directory_default_excluded(self):
        """Hidden directories are excluded by default."""
        template_path = os.path.join(custom_templates_dir, "project_template")
        args = [
            "startproject",
            "--template",
            template_path,
            "custom_project_template_hidden_directories",
            "project_dir",
        ]
        testproject_dir = os.path.join(self.test_dir, "project_dir")
        os.mkdir(testproject_dir)

        _, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        hidden_dir = os.path.join(testproject_dir, ".hidden")
        self.assertIs(os.path.exists(hidden_dir), False)