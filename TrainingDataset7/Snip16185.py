def test_must_be_logged_in(self):
        response = self.client.get(self.url, {"term": "", **self.opts})
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(self.url, {"term": "", **self.opts})
        self.assertEqual(response.status_code, 302)