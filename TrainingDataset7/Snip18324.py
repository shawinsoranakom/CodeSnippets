def test_confirm_custom_reset_url_token(self):
        url, path = self._test_confirm_start()
        path = path.replace("/reset/", "/reset/custom/token/")
        self.client.reset_url_token = "set-passwordcustom"
        response = self.client.post(
            path,
            {"new_password1": "anewpassword", "new_password2": "anewpassword"},
        )
        self.assertRedirects(response, "/reset/done/", fetch_redirect_response=False)