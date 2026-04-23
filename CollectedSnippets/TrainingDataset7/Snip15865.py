def test_custom_project_template_from_tarball_to_alternative_location(self):
        """
        Startproject can use a project template from a tarball and create it in
        a specified location.
        """
        template_path = os.path.join(custom_templates_dir, "project_template.tgz")
        args = [
            "startproject",
            "--template",
            template_path,
            "tarballtestproject",
            "altlocation",
        ]
        testproject_dir = os.path.join(self.test_dir, "altlocation")
        os.mkdir(testproject_dir)

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.isdir(testproject_dir))
        self.assertTrue(os.path.exists(os.path.join(testproject_dir, "run.py")))