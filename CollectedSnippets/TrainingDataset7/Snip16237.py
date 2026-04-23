def test_sidebar_can_be_closed(self):
        from selenium.webdriver.common.by import By

        self.selenium.get(
            self.live_server_url + reverse("test_with_sidebar:auth_user_changelist")
        )
        toggle_button = self.selenium.find_element(
            By.CSS_SELECTOR, "#toggle-nav-sidebar"
        )
        self.assertEqual(toggle_button.tag_name, "button")
        self.assertEqual(toggle_button.get_attribute("aria-label"), "Toggle navigation")
        nav_sidebar = self.selenium.find_element(By.ID, "nav-sidebar")
        self.assertEqual(nav_sidebar.get_attribute("aria-expanded"), "true")
        self.assertTrue(nav_sidebar.is_displayed())
        toggle_button.click()

        # Hidden sidebar is not visible.
        nav_sidebar = self.selenium.find_element(By.ID, "nav-sidebar")
        self.assertEqual(nav_sidebar.get_attribute("aria-expanded"), "false")
        self.assertFalse(nav_sidebar.is_displayed())
        main_element = self.selenium.find_element(By.CSS_SELECTOR, "#main")
        self.assertNotIn("shifted", main_element.get_attribute("class").split())