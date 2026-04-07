def test_suspiciousop_in_view_returns_400(self):
        response = self.client.get("/suspicious/")
        self.assertEqual(response.status_code, 400)