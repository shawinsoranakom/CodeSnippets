def test_template_dir_with_trailing_slash(self):
        "Ticket 17475: Template dir passed has a trailing path separator"
        template_path = os.path.join(custom_templates_dir, "project_template" + os.sep)
        args = ["startproject", "--template", template_path, "customtestproject"]
        testproject_dir = os.path.join(self.test_dir, "customtestproject")

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.isdir(testproject_dir))
        self.assertTrue(os.path.exists(os.path.join(testproject_dir, "additional_dir")))