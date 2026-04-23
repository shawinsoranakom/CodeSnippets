def test_basic(self):
        from selenium.webdriver.common.by import By

        self.school.students.set([self.lisa, self.peter])
        self.school.alumni.set([self.lisa, self.peter])

        with self.small_screen_size():
            self.admin_login(username="super", password="secret", login_url="/")
            self.selenium.get(
                self.live_server_url
                + reverse("admin:admin_widgets_school_change", args=(self.school.id,))
            )

            self.wait_page_ready()
            self.trigger_resize()
            self.execute_basic_operations("vertical", "students")
            self.execute_basic_operations("horizontal", "alumni")

            # Save, everything should be stored properly stored in the
            # database.
            self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
            self.wait_page_ready()
        self.school = School.objects.get(id=self.school.id)  # Reload from database
        self.assertEqual(
            list(self.school.students.all()),
            [self.arthur, self.cliff, self.jason, self.john],
        )
        self.assertEqual(
            list(self.school.alumni.all()),
            [self.arthur, self.cliff, self.jason, self.john],
        )