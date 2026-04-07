def test_logout_anonymous(self):
        # The log_out function will still trigger the signal for anonymous
        # users.
        self.client.post("/logout/next_page/")
        self.assertEqual(len(self.logged_out), 1)
        self.assertIsNone(self.logged_out[0])