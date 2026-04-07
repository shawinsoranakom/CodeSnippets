def test_post_unknown_page(self):
        "POSTing to an unknown page isn't caught as a 403 CSRF error"
        response = self.client.post("/no_such_page/")
        self.assertEqual(response.status_code, 404)