def test_access_under_login_required_middleware(self):
        reset_urls = [
            reverse("password_reset"),
            reverse("password_reset_done"),
            reverse("password_reset_confirm", kwargs={"uidb64": "abc", "token": "def"}),
            reverse("password_reset_complete"),
        ]

        for url in reset_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/password_reset/", {"email": "staffmember@example.com"}
        )
        self.assertRedirects(
            response, "/password_reset/done/", fetch_redirect_response=False
        )