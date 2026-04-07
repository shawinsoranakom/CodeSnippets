def test_skip_link_with_RTL_language_doesnt_create_horizontal_scrolling(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        with override_settings(LANGUAGE_CODE="ar"):
            self.admin_login(
                username="super",
                password="secret",
                login_url=reverse("admin:index"),
            )

            skip_link = self.selenium.find_element(
                By.CLASS_NAME, "skip-to-content-link"
            )
            body = self.selenium.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.TAB)
            self.assertTrue(skip_link.is_displayed())

            is_vertical_scrolleable = self.selenium.execute_script(
                "return arguments[0].scrollHeight > arguments[0].offsetHeight;", body
            )
            is_horizontal_scrolleable = self.selenium.execute_script(
                "return arguments[0].scrollWeight > arguments[0].offsetWeight;", body
            )
            self.assertTrue(is_vertical_scrolleable)
            self.assertFalse(is_horizontal_scrolleable)