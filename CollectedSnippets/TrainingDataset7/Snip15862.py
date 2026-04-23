def test_custom_project_template_non_python_files_not_formatted(self):
        template_path = os.path.join(custom_templates_dir, "project_template")
        args = ["startproject", "--template", template_path, "customtestproject"]
        testproject_dir = os.path.join(self.test_dir, "customtestproject")

        _, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        with open(
            os.path.join(template_path, "additional_dir", "requirements.in")
        ) as f:
            expected = f.read()
        with open(
            os.path.join(testproject_dir, "additional_dir", "requirements.in")
        ) as f:
            result = f.read()
        self.assertEqual(expected, result)