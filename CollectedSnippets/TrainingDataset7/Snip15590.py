def test_tabular_inline_m2m_widget_option_bg(self):
        from selenium.webdriver.common.by import By

        Person.objects.create(firstname="Lee")
        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_courseproxy2_add")
        )
        selector = self.selenium.find_element(By.CSS_SELECTOR, "div.selector")
        options = selector.find_elements(By.CSS_SELECTOR, "select option")
        self.assertGreater(len(options), 0)
        options[0].click()
        selector.find_element(By.CSS_SELECTOR, "p.selector-filter input").click()
        self.take_screenshot("focus_out")