def test_view_with_method_permissions(self):
        "Request a page that is protected with a @permission_required method"

        # Get the page without logging in. Should result in 302.
        response = self.client.get("/permission_protected_method_view/")
        self.assertRedirects(
            response, "/accounts/login/?next=/permission_protected_method_view/"
        )

        # Log in
        login = self.client.login(username="testclient", password="password")
        self.assertTrue(login, "Could not log in")

        # Log in with wrong permissions. Should result in 302.
        response = self.client.get("/permission_protected_method_view/")
        self.assertRedirects(
            response, "/accounts/login/?next=/permission_protected_method_view/"
        )

        permission = Permission.objects.get(
            content_type__app_label="auth", codename="add_user"
        )
        self.u1.user_permissions.add(permission)

        # Request the page again. Access is granted.
        response = self.client.get("/permission_protected_method_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].username, "testclient")