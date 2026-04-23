def test_permission_required_logged_in(self):
        self.login()
        # Already logged in...
        with self.settings(LOGIN_URL=self.do_redirect_url):
            # redirect loop encountered.
            with self.assertRaisesMessage(
                RedirectCycleError, "Redirect loop detected."
            ):
                self.client.get("/permission_required_redirect/", follow=True)
            # exception raised.
            response = self.client.get("/permission_required_exception/", follow=True)
            self.assertEqual(response.status_code, 403)
            # exception raised.
            response = self.client.get(
                "/login_and_permission_required_exception/", follow=True
            )
            self.assertEqual(response.status_code, 403)