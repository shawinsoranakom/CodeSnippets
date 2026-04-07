def test_email_not_found(self):
        """If the provided email is not registered, don't raise any error but
        also don't send any email."""
        response = self.client.get("/password_reset/")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/password_reset/", {"email": "not_a_real_email@email.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)