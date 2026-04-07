def test_add_url_not_allowed(self):
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.add_url, {})
        self.assertEqual(response.status_code, 403)