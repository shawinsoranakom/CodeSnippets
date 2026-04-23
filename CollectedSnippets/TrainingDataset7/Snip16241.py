def test_add_new_user(self):
        """A user with no password can be added.

        Enabling/disabling the usable password field shows/hides the password
        fields when adding a user.
        """
        from selenium.common import NoSuchElementException
        from selenium.webdriver.common.by import By

        user_add_url = reverse("auth_test_admin:auth_user_add")
        self.admin_login(username="super", password="secret")
        self.selenium.get(self.live_server_url + user_add_url)

        pw_switch_on = self.selenium.find_element(
            By.CSS_SELECTOR, 'input[name="usable_password"][value="true"]'
        )
        pw_switch_off = self.selenium.find_element(
            By.CSS_SELECTOR, 'input[name="usable_password"][value="false"]'
        )
        password1 = self.selenium.find_element(
            By.CSS_SELECTOR, 'input[name="password1"]'
        )
        password2 = self.selenium.find_element(
            By.CSS_SELECTOR, 'input[name="password2"]'
        )

        # Default is to set a password on user creation.
        self.assertIs(pw_switch_on.is_selected(), True)
        self.assertIs(pw_switch_off.is_selected(), False)

        # The password fields are visible.
        self.assertIs(password1.is_displayed(), True)
        self.assertIs(password2.is_displayed(), True)

        # Click to disable password-based authentication.
        pw_switch_off.click()

        # Radio buttons are updated accordingly.
        self.assertIs(pw_switch_on.is_selected(), False)
        self.assertIs(pw_switch_off.is_selected(), True)

        # The password fields are hidden.
        self.assertIs(password1.is_displayed(), False)
        self.assertIs(password2.is_displayed(), False)

        # The warning message should not be shown.
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, "id_unusable_warning")