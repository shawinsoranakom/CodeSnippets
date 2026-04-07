def test_simple_project(self):
        "Make sure the startproject management command creates a project"
        args = ["startproject", "testproject"]
        testproject_dir = os.path.join(self.test_dir, "testproject")

        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertTrue(os.path.isdir(testproject_dir))

        # running again..
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertOutput(
            err,
            "CommandError: 'testproject' conflicts with the name of an "
            "existing Python module and cannot be used as a project name. "
            "Please try another name.",
        )