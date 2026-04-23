def test_custom_project_template_exclude_directory(self):
        """
        Excluded directories (in addition to .git and __pycache__) are not
        included in the project.
        """
        template_path = os.path.join(custom_templates_dir, "project_template")
        project_name = "custom_project_with_excluded_directories"
        args = [
            "startproject",
            "--template",
            template_path,
            project_name,
            "project_dir",
            "--exclude",
            "additional_dir",
            "-x",
            ".hidden",
        ]
        testproject_dir = os.path.join(self.test_dir, "project_dir")
        os.mkdir(testproject_dir)

        _, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        excluded_directories = [
            ".hidden",
            "additional_dir",
            ".git",
            "__pycache__",
        ]
        for directory in excluded_directories:
            self.assertIs(
                os.path.exists(os.path.join(testproject_dir, directory)),
                False,
            )
        not_excluded = os.path.join(testproject_dir, project_name)
        self.assertIs(os.path.exists(not_excluded), True)