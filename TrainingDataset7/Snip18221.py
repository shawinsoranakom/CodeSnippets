def test_logout(self):
        self.client.login(username="testclient", password="password")
        self.client.post("/logout/next_page/")
        self.assertEqual(len(self.logged_out), 1)
        self.assertEqual(self.logged_out[0].username, "testclient")