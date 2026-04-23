def test_all_options_given(self):
        args = [
            "test",
            "--settings=test_project.settings",
            "--option_a=bar",
            "--option_b=foo",
            "--option_c=31337",
        ]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "bar:foo:31337")