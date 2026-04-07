def test_custom_project_template_with_non_ascii_templates(self):
        """
        The startproject management command is able to render templates with
        non-ASCII content.
        """
        template_path = os.path.join(custom_templates_dir, "project_template")
        args = [
            "startproject",
            "--template",
            template_path,
            "--extension=txt",
            "customtestproject",
        ]
        testproject_dir = os.path.join(self.test_dir, "customtestproject")

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.isdir(testproject_dir))
        path = os.path.join(testproject_dir, "ticket-18091-non-ascii-template.txt")
        with open(path, encoding="utf-8") as f:
            self.assertEqual(
                f.read().splitlines(False),
                ["Some non-ASCII text for testing ticket #18091:", "üäö €"],
            )