def test_suggestions(self):
        args = ["rnserver", "--settings=test_project.settings"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "Unknown command: 'rnserver'. Did you mean runserver?")