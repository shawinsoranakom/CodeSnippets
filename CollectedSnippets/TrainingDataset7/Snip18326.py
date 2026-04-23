def test_confirm_login_post_reset_custom_backend(self):
        # This backend is specified in the URL pattern.
        backend = "django.contrib.auth.backends.AllowAllUsersModelBackend"
        url, path = self._test_confirm_start()
        path = path.replace("/reset/", "/reset/post_reset_login_custom_backend/")
        response = self.client.post(
            path, {"new_password1": "anewpassword", "new_password2": "anewpassword"}
        )
        self.assertRedirects(response, "/reset/done/", fetch_redirect_response=False)
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertEqual(self.client.session[BACKEND_SESSION_KEY], backend)