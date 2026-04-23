def test_confirm_valid_custom_user(self):
        url, path = self._test_confirm_start()
        response = self.client.get(path)
        # redirect to a 'complete' page:
        self.assertContains(response, "Please enter your new password")
        # then submit a new password
        response = self.client.post(
            path,
            {
                "new_password1": "anewpassword",
                "new_password2": "anewpassword",
            },
        )
        self.assertRedirects(response, "/reset/done/")