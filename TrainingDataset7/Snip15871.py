def test_no_escaping_of_project_variables(self):
        "Make sure template context variables are not html escaped"
        # We're using a custom command so we need the alternate settings
        self.write_settings("alternate_settings.py")
        template_path = os.path.join(custom_templates_dir, "project_template")
        args = [
            "custom_startproject",
            "--template",
            template_path,
            "another_project",
            "project_dir",
            "--extra",
            "<&>",
            "--settings=alternate_settings",
        ]
        testproject_dir = os.path.join(self.test_dir, "project_dir")
        os.mkdir(testproject_dir)
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        test_manage_py = os.path.join(testproject_dir, "additional_dir", "extra.py")
        with open(test_manage_py) as fp:
            content = fp.read()
            self.assertIn("<&>", content)