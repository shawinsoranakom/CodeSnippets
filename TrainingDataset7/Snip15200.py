def test_collapse_filters(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))

        # The UserAdmin has 3 field filters by default: "staff status",
        # "superuser status", and "active".
        details = self.selenium.find_elements(By.CSS_SELECTOR, "details")
        # All filters are opened at first.
        for detail in details:
            self.assertTrue(detail.get_attribute("open"))
        # Collapse "staff' and "superuser" filters.
        for detail in details[:2]:
            summary = detail.find_element(By.CSS_SELECTOR, "summary")
            summary.click()
            self.assertFalse(detail.get_attribute("open"))
        # Filters are in the same state after refresh.
        self.selenium.refresh()
        self.assertFalse(
            self.selenium.find_element(
                By.CSS_SELECTOR, "[data-filter-title='staff status']"
            ).get_attribute("open")
        )
        self.assertFalse(
            self.selenium.find_element(
                By.CSS_SELECTOR, "[data-filter-title='superuser status']"
            ).get_attribute("open")
        )
        self.assertTrue(
            self.selenium.find_element(
                By.CSS_SELECTOR, "[data-filter-title='active']"
            ).get_attribute("open")
        )
        # Collapse a filter on another view (Bands).
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_changelist_band_changelist")
        )
        self.selenium.find_element(By.CSS_SELECTOR, "summary").click()
        # Go to Users view and then, back again to Bands view.
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_changelist_band_changelist")
        )
        # The filter remains in the same state.
        self.assertFalse(
            self.selenium.find_element(
                By.CSS_SELECTOR,
                "[data-filter-title='number of members']",
            ).get_attribute("open")
        )