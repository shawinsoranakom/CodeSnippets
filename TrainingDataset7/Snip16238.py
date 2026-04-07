def test_sidebar_state_persists(self):
        from selenium.webdriver.common.by import By

        self.selenium.get(
            self.live_server_url + reverse("test_with_sidebar:auth_user_changelist")
        )
        self.assertIsNone(
            self.selenium.execute_script(
                "return localStorage.getItem('django.admin.navSidebarIsOpen')"
            )
        )
        toggle_button = self.selenium.find_element(
            By.CSS_SELECTOR, "#toggle-nav-sidebar"
        )
        toggle_button.click()
        self.assertEqual(
            self.selenium.execute_script(
                "return localStorage.getItem('django.admin.navSidebarIsOpen')"
            ),
            "false",
        )
        self.selenium.get(
            self.live_server_url + reverse("test_with_sidebar:auth_user_changelist")
        )
        main_element = self.selenium.find_element(By.CSS_SELECTOR, "#main")
        self.assertNotIn("shifted", main_element.get_attribute("class").split())

        toggle_button = self.selenium.find_element(
            By.CSS_SELECTOR, "#toggle-nav-sidebar"
        )
        # Hidden sidebar is not visible.
        nav_sidebar = self.selenium.find_element(By.ID, "nav-sidebar")
        self.assertEqual(nav_sidebar.get_attribute("aria-expanded"), "false")
        self.assertFalse(nav_sidebar.is_displayed())
        toggle_button.click()
        nav_sidebar = self.selenium.find_element(By.ID, "nav-sidebar")
        self.assertEqual(nav_sidebar.get_attribute("aria-expanded"), "true")
        self.assertTrue(nav_sidebar.is_displayed())
        self.assertEqual(
            self.selenium.execute_script(
                "return localStorage.getItem('django.admin.navSidebarIsOpen')"
            ),
            "true",
        )
        self.selenium.get(
            self.live_server_url + reverse("test_with_sidebar:auth_user_changelist")
        )
        main_element = self.selenium.find_element(By.CSS_SELECTOR, "#main")
        self.assertIn("shifted", main_element.get_attribute("class").split())