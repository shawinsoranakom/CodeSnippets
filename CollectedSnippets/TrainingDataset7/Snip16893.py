def test_clearablefileinput_widget(self):
        from selenium.webdriver.common.by import By

        self._run_image_upload_path()
        self.selenium.find_element(By.ID, self.clear_checkbox_id).click()
        self._submit_and_wait()
        student = Student.objects.last()
        self.assertEqual(student.name, "Joe Doe")
        self.assertEqual(student.photo.name, "")
        # "Currently" with "Clear" checkbox and "Change" are not shown.
        photo_field_row = self.selenium.find_element(By.CSS_SELECTOR, ".field-photo")
        self.assertNotIn("Currently", photo_field_row.text)
        self.assertNotIn("Change", photo_field_row.text)