def test_guest(self):
        """If not logged in, stay on the same page."""
        response = self.client.get(self.do_redirect_url)
        self.assertEqual(response.status_code, 200)