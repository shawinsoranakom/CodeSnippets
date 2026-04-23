def test_session(self):
        "The session isn't lost if a user logs in"
        # The session doesn't exist to start.
        response = self.client.get("/check_session/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"NO")

        # This request sets a session variable.
        response = self.client.get("/set_session/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"set_session")

        # The session has been modified
        response = self.client.get("/check_session/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"YES")

        # Log in
        login = self.client.login(username="testclient", password="password")
        self.assertTrue(login, "Could not log in")

        # Session should still contain the modified value
        response = self.client.get("/check_session/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"YES")