def test_simple_project_different_directory(self):
        """
        The startproject management command creates a project in a specific
        directory.
        """
        args = ["startproject", "testproject", "othertestproject"]
        testproject_dir = os.path.join(self.test_dir, "othertestproject")
        os.mkdir(testproject_dir)

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.exists(os.path.join(testproject_dir, "manage.py")))

        # running again..
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertOutput(
            err,
            "already exists. Overlaying a project into an existing directory "
            "won't replace conflicting files.",
        )