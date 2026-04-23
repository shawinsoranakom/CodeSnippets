def test_poisoned_http_host_admin_site(self):
        """
        Poisoned HTTP_HOST headers can't be used for reset emails on admin
        views
        """
        with self.assertLogs("django.security.DisallowedHost", "ERROR"):
            response = self.client.post(
                "/admin_password_reset/",
                {"email": "staffmember@example.com"},
                headers={"host": "www.example:dr.frankenstein@evil.tld"},
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)