def test_custom_password_change_form(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin4:password_change"))
        self.assertContains(response, "Custom old password label")