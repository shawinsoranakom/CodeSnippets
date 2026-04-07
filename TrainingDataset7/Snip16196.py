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