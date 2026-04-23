def test_exception_cleared(self):
        "#5836 - A stale user exception isn't re-raised by the test client."

        login = self.client.login(username="testclient", password="password")
        self.assertTrue(login, "Could not log in")
        with self.assertRaises(CustomTestException):
            self.client.get("/staff_only/")

        # At this point, an exception has been raised, and should be cleared.

        # This next operation should be successful; if it isn't we have a
        # problem.
        login = self.client.login(username="staff", password="password")
        self.assertTrue(login, "Could not log in")
        self.client.get("/staff_only/")