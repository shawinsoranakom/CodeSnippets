def test_custom_admin_site_login_form(self):
        self.client.logout()
        response = self.client.get(reverse("admin2:index"), follow=True)
        self.assertIsInstance(response, TemplateResponse)
        self.assertEqual(response.status_code, 200)
        login = self.client.post(
            reverse("admin2:login"),
            {
                REDIRECT_FIELD_NAME: reverse("admin2:index"),
                "username": "customform",
                "password": "secret",
            },
            follow=True,
        )
        self.assertIsInstance(login, TemplateResponse)
        self.assertContains(login, "custom form error")
        self.assertContains(login, "path/to/media.css")