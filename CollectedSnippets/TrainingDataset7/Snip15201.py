def test_collapse_filter_with_unescaped_title(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        changelist_url = reverse("admin:admin_changelist_proxyuser_changelist")
        self.selenium.get(self.live_server_url + changelist_url)
        # Title is escaped.
        filter_title = self.selenium.find_element(
            By.CSS_SELECTOR, "[data-filter-title='It\\'s OK']"
        )
        filter_title.find_element(By.CSS_SELECTOR, "summary").click()
        self.assertFalse(filter_title.get_attribute("open"))
        # Filter is in the same state after refresh.
        self.selenium.refresh()
        self.assertFalse(
            self.selenium.find_element(
                By.CSS_SELECTOR, "[data-filter-title='It\\'s OK']"
            ).get_attribute("open")
        )