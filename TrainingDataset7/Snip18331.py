def test_invalid_link_if_going_directly_to_the_final_reset_password_url(self):
        url, path = self._test_confirm_start()
        _, uuidb64, _ = path.strip("/").split("/")
        response = Client().get("/reset/%s/set-password/" % uuidb64)
        self.assertContains(response, "The password reset link was invalid")