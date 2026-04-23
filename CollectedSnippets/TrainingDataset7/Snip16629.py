def test_save_button(self):
        user_count = User.objects.count()
        response = self.client.post(
            reverse("admin:auth_user_add"),
            {
                "username": "newuser",
                "password1": "newpassword",
                "password2": "newpassword",
            },
        )
        new_user = User.objects.get(username="newuser")
        self.assertRedirects(
            response, reverse("admin:auth_user_change", args=(new_user.pk,))
        )
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertTrue(new_user.has_usable_password())