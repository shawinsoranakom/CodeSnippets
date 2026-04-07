def test_wrong_nl_prefix(self):
        response = self.client.get("/nl/account/register/")
        self.assertEqual(response.status_code, 404)