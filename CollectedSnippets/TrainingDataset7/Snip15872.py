def test_custom_project_destination_missing(self):
        """
        Create the directory when the provided destination directory doesn't
        exist.
        """
        template_path = os.path.join(custom_templates_dir, "project_template")
        args = [
            "startproject",
            "--template",
            template_path,
            "yet_another_project",
            "project_dir2",
        ]
        testproject_dir = os.path.join(self.test_dir, "project_dir2")
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertNoOutput(err)
        self.assertTrue(os.path.exists(testproject_dir))