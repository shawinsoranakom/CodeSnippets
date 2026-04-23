def test_confirm_redirect_default(self):
        url, path = self._test_confirm_start()
        response = self.client.post(
            path, {"new_password1": "anewpassword", "new_password2": "anewpassword"}
        )
        self.assertRedirects(response, "/reset/done/", fetch_redirect_response=False)