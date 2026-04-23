def test_login_button_centered(self):
        from selenium.webdriver.common.by import By

        self.selenium.get(self.live_server_url + reverse("admin:login"))
        button = self.selenium.find_element(By.CSS_SELECTOR, ".submit-row input")
        offset_left = button.get_property("offsetLeft")
        offset_right = button.get_property("offsetParent").get_property(
            "offsetWidth"
        ) - (offset_left + button.get_property("offsetWidth"))
        # Use assertAlmostEqual to avoid pixel rounding errors.
        self.assertAlmostEqual(offset_left, offset_right, delta=3)
        self.take_screenshot("login")