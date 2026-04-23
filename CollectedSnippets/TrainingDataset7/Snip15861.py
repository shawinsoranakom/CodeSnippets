def test_custom_project_template(self):
        """
        The startproject management command is able to use a different project
        template.
        """
        template_path = os.path.join(custom_templates_dir, "project_template")
        args = ["startproject", "--template", template_path, "customtestproject"]
        testproject_dir = os.path.join(self.test_dir, "customtestproject")

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.isdir(testproject_dir))
        self.assertTrue(os.path.exists(os.path.join(testproject_dir, "additional_dir")))