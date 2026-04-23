def test_messages(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        with override_settings(MESSAGE_LEVEL=10):
            self.admin_login(
                username="super", password="secret", login_url=reverse("admin:index")
            )
            UserMessenger.objects.create()
            for level in ["warning", "info", "error", "success", "debug"]:
                self.selenium.get(
                    self.live_server_url
                    + reverse("admin:admin_views_usermessenger_changelist"),
                )
                checkbox = self.selenium.find_element(
                    By.CSS_SELECTOR, "tr input.action-select"
                )
                checkbox.click()
                Select(self.selenium.find_element(By.NAME, "action")).select_by_value(
                    f"message_{level}"
                )
                self.selenium.find_element(By.XPATH, '//button[text()="Run"]').click()
                message = self.selenium.find_element(
                    By.CSS_SELECTOR, "ul.messagelist li"
                )
                self.assertEqual(message.get_attribute("innerText"), f"Test {level}")
                self.take_screenshot(level)