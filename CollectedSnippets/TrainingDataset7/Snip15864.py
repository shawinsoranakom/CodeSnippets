def test_custom_project_template_from_tarball_by_path(self):
        """
        The startproject management command is able to use a different project
        template from a tarball.
        """
        template_path = os.path.join(custom_templates_dir, "project_template.tgz")
        args = ["startproject", "--template", template_path, "tarballtestproject"]
        testproject_dir = os.path.join(self.test_dir, "tarballtestproject")

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.isdir(testproject_dir))
        self.assertTrue(os.path.exists(os.path.join(testproject_dir, "run.py")))