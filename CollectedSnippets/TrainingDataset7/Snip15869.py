def test_file_without_extension(self):
        """
        Make sure the startproject management command is able to render custom
        files
        """
        template_path = os.path.join(custom_templates_dir, "project_template")
        args = [
            "startproject",
            "--template",
            template_path,
            "customtestproject",
            "-e",
            "txt",
            "-n",
            "Procfile",
        ]
        testproject_dir = os.path.join(self.test_dir, "customtestproject")

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.isdir(testproject_dir))
        self.assertTrue(os.path.exists(os.path.join(testproject_dir, "additional_dir")))
        base_path = os.path.join(testproject_dir, "additional_dir")
        for f in ("Procfile", "additional_file.py", "requirements.txt"):
            self.assertTrue(os.path.exists(os.path.join(base_path, f)))
            with open(os.path.join(base_path, f)) as fh:
                self.assertEqual(
                    fh.read().strip(), "# some file for customtestproject test project"
                )