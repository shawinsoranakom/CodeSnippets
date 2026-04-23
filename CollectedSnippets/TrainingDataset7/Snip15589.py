def test_tabular_inline_with_filter_horizontal(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_courseproxy2_add")
        )
        m2m_widget = self.selenium.find_element(By.CSS_SELECTOR, "div.selector")
        self.assertTrue(m2m_widget.is_displayed())
        self.take_screenshot("tabular")