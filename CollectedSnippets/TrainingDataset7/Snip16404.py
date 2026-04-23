def test_login_page_notice_for_non_staff_users(self):
        """
        A logged-in non-staff user trying to access the admin index should be
        presented with the login page and a hint indicating that the current
        user doesn't have access to it.
        """
        hint_template = "You are authenticated as {}"

        # Anonymous user should not be shown the hint
        response = self.client.get(self.index_url, follow=True)
        self.assertContains(response, "login-form")
        self.assertNotContains(response, hint_template.format(""), status_code=200)

        # Non-staff user should be shown the hint
        self.client.force_login(self.nostaffuser)
        response = self.client.get(self.index_url, follow=True)
        self.assertContains(response, "login-form")
        self.assertContains(
            response, hint_template.format(self.nostaffuser.username), status_code=200
        )