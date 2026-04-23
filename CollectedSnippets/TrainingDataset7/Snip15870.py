def test_custom_project_template_context_variables(self):
        "Make sure template context variables are rendered with proper values"
        template_path = os.path.join(custom_templates_dir, "project_template")
        args = [
            "startproject",
            "--template",
            template_path,
            "another_project",
            "project_dir",
        ]
        testproject_dir = os.path.join(self.test_dir, "project_dir")
        os.mkdir(testproject_dir)
        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        test_manage_py = os.path.join(testproject_dir, "manage.py")
        with open(test_manage_py) as fp:
            content = fp.read()
            self.assertInAfterFormatting('project_name = "another_project"', content)
            self.assertInAfterFormatting(
                'project_directory = "%s"' % testproject_dir, content
            )