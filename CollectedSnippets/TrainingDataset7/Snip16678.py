def test_logout(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse("admin:logout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/logged_out.html")
        self.assertEqual(response.request["PATH_INFO"], reverse("admin:logout"))
        self.assertFalse(response.context["has_permission"])
        self.assertNotContains(
            response, "user-tools"
        )