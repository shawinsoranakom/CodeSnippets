def test_option_name_and_value_separated(self):
        args = ["test", "--settings=test_project.settings", "--option_b", "foo"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "1:foo:3")