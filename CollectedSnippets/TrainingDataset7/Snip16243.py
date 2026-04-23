def test_fieldset_legend_wide_alignment(self):
        user_add_url = reverse("auth_test_admin:auth_user_add")
        self.admin_login(username="super", password="secret")
        self.selenium.get(self.live_server_url + user_add_url)

        # The fieldset legend is aligned with other fields.
        self.take_screenshot("fieldset_legend_wide")