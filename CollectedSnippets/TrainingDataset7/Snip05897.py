def admin_login(self, username, password, login_url="/admin/"):
        """
        Log in to the admin.
        """
        from selenium.webdriver.common.by import By

        self.selenium.get("%s%s" % (self.live_server_url, login_url))
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys(username)
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys(password)
        login_text = _("Log in")
        with self.wait_page_loaded():
            self.selenium.find_element(
                By.XPATH, '//input[@value="%s"]' % login_text
            ).click()