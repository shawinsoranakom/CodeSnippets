def test_clearablefileinput_widget_preserve_clear_checkbox(self):
        from selenium.webdriver.common.by import By

        self._run_image_upload_path()
        # "Clear" is not checked by default.
        self.assertIs(
            self.selenium.find_element(By.ID, self.clear_checkbox_id).is_selected(),
            False,
        )
        # "Clear" was checked, but a validation error is raised.
        name_input = self.selenium.find_element(By.ID, self.name_input_id)
        name_input.clear()
        self.selenium.find_element(By.ID, self.clear_checkbox_id).click()
        self._submit_and_wait()
        self.assertEqual(
            self.selenium.find_element(By.CSS_SELECTOR, ".errorlist li").text,
            "This field is required.",
        )
        # "Clear" persists checked.
        self.assertIs(
            self.selenium.find_element(By.ID, self.clear_checkbox_id).is_selected(),
            True,
        )