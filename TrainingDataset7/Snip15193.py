def test_add_row_selection(self):
        """
        The status line for selected rows gets updated correctly (#22038).
        """
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))

        form_id = "#changelist-form"

        # Test amount of rows in the Changelist
        rows = self.selenium.find_elements(
            By.CSS_SELECTOR, "%s #result_list tbody tr" % form_id
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]

        selection_indicator = self.selenium.find_element(
            By.CSS_SELECTOR, "%s .action-counter" % form_id
        )
        all_selector = self.selenium.find_element(By.ID, "action-toggle")
        row_selector = self.selenium.find_element(
            By.CSS_SELECTOR,
            "%s #result_list tbody tr:first-child .action-select" % form_id,
        )

        # Test current selection
        self.assertEqual(selection_indicator.text, "0 of 1 selected")
        self.assertIs(all_selector.get_property("checked"), False)
        self.assertEqual(row.get_attribute("class"), "")

        # Select a row and check again
        row_selector.click()
        self.assertEqual(selection_indicator.text, "1 of 1 selected")
        self.assertIs(all_selector.get_property("checked"), True)
        self.assertEqual(row.get_attribute("class"), "selected")

        # Deselect a row and check again
        row_selector.click()
        self.assertEqual(selection_indicator.text, "0 of 1 selected")
        self.assertIs(all_selector.get_property("checked"), False)
        self.assertEqual(row.get_attribute("class"), "")