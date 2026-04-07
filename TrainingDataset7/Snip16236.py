def test_sidebar_starts_open(self):
        from selenium.webdriver.common.by import By

        self.selenium.get(
            self.live_server_url + reverse("test_with_sidebar:auth_user_changelist")
        )
        main_element = self.selenium.find_element(By.CSS_SELECTOR, "#main")
        self.assertIn("shifted", main_element.get_attribute("class").split())