def test_view_with_permissions_exception(self):
        """
        Request a page that is protected with @permission_required but raises
        an exception.
        """

        # Get the page without logging in. Should result in 403.
        response = self.client.get("/permission_protected_view_exception/")
        self.assertEqual(response.status_code, 403)

        # Log in
        login = self.client.login(username="testclient", password="password")
        self.assertTrue(login, "Could not log in")

        # Log in with wrong permissions. Should result in 403.
        response = self.client.get("/permission_protected_view_exception/")
        self.assertEqual(response.status_code, 403)