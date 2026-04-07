def test_form_url_present_in_context(self):
        u = User.objects.all()[0]
        response = self.client.get(
            reverse("admin3:auth_user_password_change", args=(u.pk,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form_url"], "pony")