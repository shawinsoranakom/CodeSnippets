def test_clearablefileinput_widget_invalid_file(self):
        from selenium.webdriver.common.by import By

        self._run_image_upload_path()
        # Uploading non-image files is not supported by Safari with Selenium,
        # so upload a broken one instead.
        photo_input = self.selenium.find_element(By.ID, self.photo_input_id)
        photo_input.send_keys(f"{self.tests_files_folder}/brokenimg.png")
        self._submit_and_wait()
        self.assertEqual(
            self.selenium.find_element(By.CSS_SELECTOR, ".errorlist li").text,
            (
                "Upload a valid image. The file you uploaded was either not an image "
                "or a corrupted image."
            ),
        )
        # "Currently" with "Clear" checkbox and "Change" still shown.
        photo_field_row = self.selenium.find_element(By.CSS_SELECTOR, ".field-photo")
        self.assertIn("Currently", photo_field_row.text)
        self.assertIn("Change", photo_field_row.text)