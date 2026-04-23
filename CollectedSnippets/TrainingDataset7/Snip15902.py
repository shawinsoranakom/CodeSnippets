def test_no_suggestions(self):
        args = ["abcdef", "--settings=test_project.settings"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertNotInOutput(err, "Did you mean")