def test_sidebar_filter_persists(self):
        from selenium.webdriver.common.by import By

        self.selenium.get(
            self.live_server_url + reverse("test_with_sidebar:auth_user_changelist")
        )
        filter_value_script = (
            "return sessionStorage.getItem('django.admin.navSidebarFilterValue')"
        )
        self.assertIsNone(self.selenium.execute_script(filter_value_script))
        filter_input = self.selenium.find_element(By.CSS_SELECTOR, "#nav-filter")
        filter_input.send_keys("users")
        self.assertEqual(self.selenium.execute_script(filter_value_script), "users")