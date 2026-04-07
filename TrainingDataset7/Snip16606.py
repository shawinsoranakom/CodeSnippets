def test_user_password_change_limited_queryset(self):
        su = User.objects.filter(is_superuser=True)[0]
        response = self.client.get(
            reverse("admin2:auth_user_password_change", args=(su.pk,))
        )
        self.assertEqual(response.status_code, 404)