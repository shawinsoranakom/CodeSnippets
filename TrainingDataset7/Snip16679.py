def test_client_logout_url_can_be_used_to_login(self):
        response = self.client.post(reverse("admin:logout"))
        self.assertEqual(
            response.status_code, 302
        )  # we should be redirected to the login page.

        # follow the redirect and test results.
        response = self.client.post(reverse("admin:logout"), follow=True)
        self.assertContains(
            response,
            '<input type="hidden" name="next" value="%s">' % reverse("admin:index"),
        )
        self.assertTemplateUsed(response, "admin/login.html")
        self.assertEqual(response.request["PATH_INFO"], reverse("admin:login"))