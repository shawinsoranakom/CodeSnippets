def test_save_continue_editing_button(self):
        user_count = User.objects.count()
        response = self.client.post(
            reverse("admin:auth_user_add"),
            {
                "username": "newuser",
                "password1": "newpassword",
                "password2": "newpassword",
                "_continue": "1",
            },
        )
        new_user = User.objects.get(username="newuser")
        new_user_url = reverse("admin:auth_user_change", args=(new_user.pk,))
        self.assertRedirects(response, new_user_url, fetch_redirect_response=False)
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertTrue(new_user.has_usable_password())
        response = self.client.get(new_user_url)
        self.assertContains(
            response,
            '<li class="success">The user “<a href="%s">'
            "%s</a>” was added successfully. You may edit it again below.</li>"
            % (new_user_url, new_user),
            html=True,
        )