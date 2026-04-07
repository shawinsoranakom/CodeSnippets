def test_inline_add_another_widgets(self):
        from selenium.webdriver.common.by import By

        def assertNoResults(row):
            elem = row.find_element(By.CSS_SELECTOR, ".select2-selection")
            with self.select2_ajax_wait():
                elem.click()  # Open the autocomplete dropdown.
            results = self.selenium.find_element(By.CSS_SELECTOR, ".select2-results")
            self.assertTrue(results.is_displayed())
            option = self.selenium.find_element(
                By.CSS_SELECTOR, ".select2-results__option"
            )
            self.assertEqual(option.text, "No results found")

        # Autocomplete works in rows present when the page loads.
        self.selenium.get(
            self.live_server_url + reverse("autocomplete_admin:admin_views_book_add")
        )
        rows = self.selenium.find_elements(By.CSS_SELECTOR, ".dynamic-authorship_set")
        self.assertEqual(len(rows), 3)
        assertNoResults(rows[0])
        # Autocomplete works in rows added using the "Add another" button.
        self.selenium.find_element(By.LINK_TEXT, "Add another Authorship").click()
        rows = self.selenium.find_elements(By.CSS_SELECTOR, ".dynamic-authorship_set")
        self.assertEqual(len(rows), 4)
        assertNoResults(rows[-1])