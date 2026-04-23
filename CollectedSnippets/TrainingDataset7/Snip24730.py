def test_bad_request_in_view_returns_400(self):
        response = self.client.get("/bad_request/")
        self.assertEqual(response.status_code, 400)