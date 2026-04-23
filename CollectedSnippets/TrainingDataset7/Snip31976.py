def test_clearsessions_unsupported(self):
        msg = (
            "Session engine 'sessions_tests.no_clear_expired' doesn't "
            "support clearing expired sessions."
        )
        with self.settings(SESSION_ENGINE="sessions_tests.no_clear_expired"):
            with self.assertRaisesMessage(management.CommandError, msg):
                management.call_command("clearsessions")