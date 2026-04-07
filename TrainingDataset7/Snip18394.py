def test_permission_required_not_logged_in(self):
        # Not logged in ...
        with self.settings(LOGIN_URL=self.do_redirect_url):
            # redirected to login.
            response = self.client.get("/permission_required_redirect/", follow=True)
            self.assertEqual(response.status_code, 200)
            # exception raised.
            response = self.client.get("/permission_required_exception/", follow=True)
            self.assertEqual(response.status_code, 403)
            # redirected to login.
            response = self.client.get(
                "/login_and_permission_required_exception/", follow=True
            )
            self.assertEqual(response.status_code, 200)