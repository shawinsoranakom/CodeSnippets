def test_confirm_login_post_reset(self):
        url, path = self._test_confirm_start()
        path = path.replace("/reset/", "/reset/post_reset_login/")
        response = self.client.post(
            path, {"new_password1": "anewpassword", "new_password2": "anewpassword"}
        )
        self.assertRedirects(response, "/reset/done/", fetch_redirect_response=False)
        self.assertIn(SESSION_KEY, self.client.session)