def test_select(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import Select

        self.selenium.get(
            self.live_server_url + reverse("autocomplete_admin:admin_views_answer_add")
        )
        elem = self.selenium.find_element(By.CSS_SELECTOR, ".select2-selection")
        with self.select2_ajax_wait():
            elem.click()  # Open the autocomplete dropdown.
        results = self.selenium.find_element(By.CSS_SELECTOR, ".select2-results")
        self.assertTrue(results.is_displayed())
        option = self.selenium.find_element(By.CSS_SELECTOR, ".select2-results__option")
        self.assertEqual(option.text, "No results found")
        with self.select2_ajax_wait():
            elem.click()  # Close the autocomplete dropdown.
        q1 = Question.objects.create(question="Who am I?")
        Question.objects.bulk_create(
            Question(question=str(i)) for i in range(PAGINATOR_SIZE + 10)
        )
        with self.select2_ajax_wait():
            elem.click()  # Reopen the dropdown now that some objects exist.
        result_container = self.selenium.find_element(
            By.CSS_SELECTOR, ".select2-results"
        )
        self.assertTrue(result_container.is_displayed())
        # PAGINATOR_SIZE results and "Loading more results".
        self.assertCountSeleniumElements(
            ".select2-results__option",
            PAGINATOR_SIZE + 1,
            root_element=result_container,
        )
        search = self.selenium.find_element(By.CSS_SELECTOR, ".select2-search__field")
        # Load next page of results by scrolling to the bottom of the list.
        for _ in range(PAGINATOR_SIZE + 1):
            with self.select2_ajax_wait():
                search.send_keys(Keys.ARROW_DOWN)
        # All objects are now loaded.
        self.assertCountSeleniumElements(
            ".select2-results__option",
            PAGINATOR_SIZE + 11,
            root_element=result_container,
        )
        # Limit the results with the search field.
        with self.select2_ajax_wait():
            search.send_keys("Who")
            # Ajax request is delayed.
            self.assertTrue(result_container.is_displayed())
            self.assertCountSeleniumElements(
                ".select2-results__option",
                PAGINATOR_SIZE + 12,
                root_element=result_container,
            )
        self.assertTrue(result_container.is_displayed())
        self.assertCountSeleniumElements(
            ".select2-results__option", 1, root_element=result_container
        )
        # Select the result.
        with self.select2_ajax_wait():
            search.send_keys(Keys.RETURN)
        select = Select(self.selenium.find_element(By.ID, "id_question"))
        self.assertEqual(
            select.first_selected_option.get_attribute("value"), str(q1.pk)
        )