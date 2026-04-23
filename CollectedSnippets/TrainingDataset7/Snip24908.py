def test_not_prefixed_redirect(self):
        response = self.client.get("/not-prefixed", headers={"accept-language": "en"})
        self.assertEqual(response.status_code, 404)