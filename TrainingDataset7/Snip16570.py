def test_collapsible_fieldset(self):
        """
        The 'collapse' class in fieldsets definition allows to
        show/hide the appropriate field section.
        """
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_article_add")
        )
        self.assertFalse(self.selenium.find_element(By.ID, "id_title").is_displayed())
        self.take_screenshot("collapsed")
        self.selenium.find_elements(By.TAG_NAME, "summary")[0].click()
        self.assertTrue(self.selenium.find_element(By.ID, "id_title").is_displayed())
        self.take_screenshot("expanded")