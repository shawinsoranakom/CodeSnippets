def test_save_add_another_button(self):
        user_count = User.objects.count()
        response = self.client.post(
            reverse("admin:auth_user_add"),
            {
                "username": "newuser",
                "password1": "newpassword",
                "password2": "newpassword",
                "_addanother": "1",
            },
        )
        new_user = User.objects.order_by("-id")[0]
        self.assertRedirects(response, reverse("admin:auth_user_add"))
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertTrue(new_user.has_usable_password())