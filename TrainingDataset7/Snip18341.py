def test_confirm_invalid_uuid(self):
        """A uidb64 that decodes to a non-UUID doesn't crash."""
        _, path = self._test_confirm_start()
        invalid_uidb64 = urlsafe_base64_encode(b"INVALID_UUID")
        first, _uuidb64_, second = path.strip("/").split("/")
        response = self.client.get(
            "/" + "/".join((first, invalid_uidb64, second)) + "/"
        )
        self.assertContains(response, "The password reset link was invalid")