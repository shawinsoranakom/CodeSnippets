def test_default_options(self):
        args = ["test", "--settings=test_project.settings"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "1:2:3")