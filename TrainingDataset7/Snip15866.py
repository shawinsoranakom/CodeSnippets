def test_custom_project_template_from_tarball_by_url(self):
        """
        The startproject management command is able to use a different project
        template from a tarball via a URL.
        """
        template_url = "%s/custom_templates/project_template.tgz" % self.live_server_url

        args = ["startproject", "--template", template_url, "urltestproject"]
        testproject_dir = os.path.join(self.test_dir, "urltestproject")

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.isdir(testproject_dir))
        self.assertTrue(os.path.exists(os.path.join(testproject_dir, "run.py")))