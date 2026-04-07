def test_empty_allowed_hosts_error(self):
        out, err = self.run_manage(["runserver"])
        self.assertNoOutput(out)
        self.assertOutput(
            err, "CommandError: You must set settings.ALLOWED_HOSTS if DEBUG is False."
        )