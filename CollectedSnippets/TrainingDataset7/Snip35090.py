def test_ticket_17477(self):
        """'manage.py help test' works after r16352."""
        args = ["help", "test"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)