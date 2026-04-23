def test_confirm_redirect_custom(self):
        url, path = self._test_confirm_start()
        path = path.replace("/reset/", "/reset/custom/")
        response = self.client.post(
            path, {"new_password1": "anewpassword", "new_password2": "anewpassword"}
        )
        self.assertRedirects(response, "/custom/", fetch_redirect_response=False)