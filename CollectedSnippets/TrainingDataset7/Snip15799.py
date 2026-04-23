def test_suppressed_options(self):
        """runserver doesn't support --verbosity and --trackback options."""
        out, err = self.run_manage(["runserver", "--help"])
        self.assertNotInOutput(out, "--verbosity")
        self.assertNotInOutput(out, "--trackback")
        self.assertOutput(out, "--settings")