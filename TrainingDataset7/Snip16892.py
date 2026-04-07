def _run_image_upload_path(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret", login_url="/")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_widgets_student_add"),
        )
        # Add a student.
        name_input = self.selenium.find_element(By.ID, self.name_input_id)
        name_input.send_keys("Joe Doe")
        photo_input = self.selenium.find_element(By.ID, self.photo_input_id)
        photo_input.send_keys(f"{self.tests_files_folder}/test.png")
        self._submit_and_wait()
        student = Student.objects.last()
        self.assertEqual(student.name, "Joe Doe")
        self.assertRegex(student.photo.name, r"^photos\/(test|test_.+).png")