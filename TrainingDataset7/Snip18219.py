def test_login(self):
        # Only a successful login will trigger the success signal.
        self.client.login(username="testclient", password="bad")
        self.assertEqual(len(self.logged_in), 0)
        self.assertEqual(len(self.login_failed), 1)
        self.assertEqual(self.login_failed[0]["credentials"]["username"], "testclient")
        # verify the password is cleansed
        self.assertIn("***", self.login_failed[0]["credentials"]["password"])
        self.assertIn("request", self.login_failed[0])

        # Like this:
        self.client.login(username="testclient", password="password")
        self.assertEqual(len(self.logged_in), 1)
        self.assertEqual(self.logged_in[0].username, "testclient")

        # Ensure there were no more failures.
        self.assertEqual(len(self.login_failed), 1)