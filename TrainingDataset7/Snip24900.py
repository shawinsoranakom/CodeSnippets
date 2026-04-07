def test_nl_redirect_wrong_url(self):
        response = self.client.get(
            "/account/register/", headers={"accept-language": "nl"}
        )
        self.assertEqual(response.status_code, 404)