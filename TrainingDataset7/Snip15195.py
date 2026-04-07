def test_selection_counter_is_synced_when_page_is_shown(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(self.live_server_url + reverse("admin:auth_user_changelist"))

        form_id = "#changelist-form"
        first_row_checkbox_selector = (
            f"{form_id} #result_list tbody tr:first-child .action-select"
        )
        selection_indicator_selector = f"{form_id} .action-counter"
        selection_indicator = self.selenium.find_element(
            By.CSS_SELECTOR, selection_indicator_selector
        )
        row_checkbox = self.selenium.find_element(
            By.CSS_SELECTOR, first_row_checkbox_selector
        )
        # Select a row.
        row_checkbox.click()
        self.assertEqual(selection_indicator.text, "1 of 1 selected")
        # Go to another page and get back.
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_changelist_parent_changelist")
        )
        self.selenium.back()
        # The selection indicator is synced with the selected checkboxes.
        selection_indicator = self.selenium.find_element(
            By.CSS_SELECTOR, selection_indicator_selector
        )
        row_checkbox = self.selenium.find_element(
            By.CSS_SELECTOR, first_row_checkbox_selector
        )
        selected_rows = 1 if row_checkbox.is_selected() else 0
        self.assertEqual(selection_indicator.text, f"{selected_rows} of 1 selected")