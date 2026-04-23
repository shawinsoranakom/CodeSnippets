def test_add_stackeds(self):
        """
        The "Add another XXX" link correctly adds items to the stacked formset.
        """
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_holder4_add")
        )

        inline_id = "#inner4stacked_set-group"
        rows_selector = "%s .dynamic-inner4stacked_set" % inline_id

        self.assertCountSeleniumElements(rows_selector, 3)
        add_button = self.selenium.find_element(
            By.LINK_TEXT, "Add another Inner4 stacked"
        )
        add_button.click()
        self.assertCountSeleniumElements(rows_selector, 4)
        self.take_screenshot("added")