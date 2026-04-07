def test_user_change_password_passes_user_to_has_change_permission(
        self, has_change_permission
    ):
        url = reverse(
            "auth_test_admin:auth_user_password_change", args=(self.admin.pk,)
        )
        self.client.post(url, {"password1": "password1", "password2": "password1"})
        (_request, user), _kwargs = has_change_permission.call_args
        self.assertEqual(user.pk, self.admin.pk)