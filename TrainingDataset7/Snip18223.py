def test_failed_login_without_request(self):
        authenticate(username="testclient", password="bad")
        self.assertIsNone(self.login_failed[0]["request"])