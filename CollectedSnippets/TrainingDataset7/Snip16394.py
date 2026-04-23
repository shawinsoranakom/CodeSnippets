def test_pwd_change_custom_template(self):
        self.client.force_login(self.superuser)
        su = User.objects.get(username="super")
        response = self.client.get(
            reverse("admin4:auth_user_password_change", args=(su.pk,))
        )
        self.assertEqual(response.status_code, 200)