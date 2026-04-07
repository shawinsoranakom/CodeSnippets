def test_delete_invalid_stacked_inlines(self):
        from selenium.common.exceptions import NoSuchElementException
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_holder4_add")
        )

        inline_id = "#inner4stacked_set-group"
        rows_selector = "%s .dynamic-inner4stacked_set" % inline_id

        self.assertCountSeleniumElements(rows_selector, 3)

        add_button = self.selenium.find_element(
            By.LINK_TEXT,
            "Add another Inner4 stacked",
        )
        add_button.click()
        add_button.click()
        self.assertCountSeleniumElements("#id_inner4stacked_set-4-dummy", 1)

        # Enter some data and click 'Save'.
        self.selenium.find_element(By.NAME, "dummy").send_keys("1")
        self.selenium.find_element(By.NAME, "inner4stacked_set-0-dummy").send_keys(
            "100"
        )
        self.selenium.find_element(By.NAME, "inner4stacked_set-1-dummy").send_keys(
            "101"
        )
        self.selenium.find_element(By.NAME, "inner4stacked_set-2-dummy").send_keys(
            "222"
        )
        self.selenium.find_element(By.NAME, "inner4stacked_set-3-dummy").send_keys(
            "103"
        )
        self.selenium.find_element(By.NAME, "inner4stacked_set-4-dummy").send_keys(
            "222"
        )
        with self.wait_page_loaded():
            self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()

        # Sanity check.
        self.assertCountSeleniumElements(rows_selector, 5)
        errorlist = self.selenium.find_element(
            By.CSS_SELECTOR,
            "%s .dynamic-inner4stacked_set .errorlist li" % inline_id,
        )
        self.assertEqual("Please correct the duplicate values below.", errorlist.text)
        delete_link = self.selenium.find_element(
            By.CSS_SELECTOR, "#inner4stacked_set-4 .inline-deletelink"
        )
        delete_link.click()
        self.assertCountSeleniumElements(rows_selector, 4)
        with self.disable_implicit_wait(), self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.CSS_SELECTOR,
                "%s .dynamic-inner4stacked_set .errorlist li" % inline_id,
            )

        with self.wait_page_loaded():
            self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()

        # The objects have been created in the database.
        self.assertEqual(Inner4Stacked.objects.count(), 4)