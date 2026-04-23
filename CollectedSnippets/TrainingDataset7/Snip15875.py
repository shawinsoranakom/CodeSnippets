def test_custom_project_template_hidden_directory_included(self):
        """
        Template context variables in hidden directories are rendered, if not
        excluded.
        """
        template_path = os.path.join(custom_templates_dir, "project_template")
        project_name = "custom_project_template_hidden_directories_included"
        args = [
            "startproject",
            "--template",
            template_path,
            project_name,
            "project_dir",
            "--exclude",
        ]
        testproject_dir = os.path.join(self.test_dir, "project_dir")
        os.mkdir(testproject_dir)

        _, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        render_py_path = os.path.join(testproject_dir, ".hidden", "render.py")
        with open(render_py_path) as fp:
            self.assertInAfterFormatting(
                f"# The {project_name} should be rendered.",
                fp.read(),
            )