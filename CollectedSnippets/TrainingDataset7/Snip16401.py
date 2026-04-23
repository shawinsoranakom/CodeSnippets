def test_login_has_permission(self):
        # Regular User should not be able to login.
        response = self.client.get(reverse("has_permission_admin:index"))
        self.assertEqual(response.status_code, 302)
        login = self.client.post(
            reverse("has_permission_admin:login"), self.joepublic_login
        )
        self.assertContains(login, "permission denied")

        # User with permissions should be able to login.
        response = self.client.get(reverse("has_permission_admin:index"))
        self.assertEqual(response.status_code, 302)
        login = self.client.post(
            reverse("has_permission_admin:login"), self.nostaff_login
        )
        self.assertRedirects(login, reverse("has_permission_admin:index"))
        self.assertFalse(login.context)
        self.client.post(reverse("has_permission_admin:logout"))

        # Staff should be able to login.
        response = self.client.get(reverse("has_permission_admin:index"))
        self.assertEqual(response.status_code, 302)
        login = self.client.post(
            reverse("has_permission_admin:login"),
            {
                REDIRECT_FIELD_NAME: reverse("has_permission_admin:index"),
                "username": "deleteuser",
                "password": "secret",
            },
        )
        self.assertRedirects(login, reverse("has_permission_admin:index"))
        self.assertFalse(login.context)
        self.client.post(reverse("has_permission_admin:logout"))