def test_delete_inlines(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_profilecollection_add")
        )

        # Add a few inlines
        self.selenium.find_element(By.LINK_TEXT, "Add another Profile").click()
        self.selenium.find_element(By.LINK_TEXT, "Add another Profile").click()
        self.selenium.find_element(By.LINK_TEXT, "Add another Profile").click()
        self.selenium.find_element(By.LINK_TEXT, "Add another Profile").click()
        self.assertCountSeleniumElements(
            "#profile_set-group table tr.dynamic-profile_set", 5
        )
        self.assertCountSeleniumElements(
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-0", 1
        )
        self.assertCountSeleniumElements(
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-1", 1
        )
        self.assertCountSeleniumElements(
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-2", 1
        )
        self.assertCountSeleniumElements(
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-3", 1
        )
        self.assertCountSeleniumElements(
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-4", 1
        )
        # Click on a few delete buttons
        self.selenium.find_element(
            By.CSS_SELECTOR,
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-1 "
            "td.delete a",
        ).click()
        self.selenium.find_element(
            By.CSS_SELECTOR,
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-2 "
            "td.delete a",
        ).click()
        # The rows are gone and the IDs have been re-sequenced
        self.assertCountSeleniumElements(
            "#profile_set-group table tr.dynamic-profile_set", 3
        )
        self.assertCountSeleniumElements(
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-0", 1
        )
        self.assertCountSeleniumElements(
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-1", 1
        )
        self.assertCountSeleniumElements(
            "form#profilecollection_form tr.dynamic-profile_set#profile_set-2", 1
        )