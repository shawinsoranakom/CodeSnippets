def test_timezone_warning_message(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret", login_url="/")

        self.selenium.get(
            self.live_server_url + reverse("admin:admin_widgets_member_add")
        )

        datetime = self.selenium.find_element(By.CSS_SELECTOR, "p.datetime")
        warnings = self.selenium.find_elements(
            By.CSS_SELECTOR, "div.field-birthdate div.timezonewarning"
        )
        self.assertEqual(len(warnings), 1)

        warning = warnings[0]
        self.assertTrue(warning.is_displayed())
        next_element = warning.find_element(By.XPATH, "./following-sibling::*[1]")
        # Warning messages are generally located just above the field block.
        self.assertEqual(next_element, datetime)

        date = datetime.find_element(By.TAG_NAME, "input")
        date.send_keys("invalid")
        with self.wait_page_loaded():
            self.selenium.find_element(By.NAME, "_save").click()

        errors = self.selenium.find_element(By.ID, "id_birthdate_error")
        warning = self.selenium.find_element(
            By.CSS_SELECTOR, "div.help.timezonewarning"
        )
        next_element = warning.find_element(By.XPATH, "./following-sibling::*[1]")
        # warning message appears above the error message.
        self.assertEqual(next_element, errors)