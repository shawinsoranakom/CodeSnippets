def test_follow_relative_redirect(self):
        "A URL with a relative redirect can be followed."
        response = self.client.get("/accounts/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/accounts/login/")