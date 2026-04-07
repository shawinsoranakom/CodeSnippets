def test_back_button_bug(self):
        """
        Some browsers had a bug where navigating away from the change page
        and then clicking the browser's back button would clear the
        filter_horizontal/filter_vertical widgets (#13614).
        """
        from selenium.webdriver.common.by import By

        self.school.students.set([self.lisa, self.peter])
        self.school.alumni.set([self.lisa, self.peter])
        self.admin_login(username="super", password="secret", login_url="/")
        change_url = reverse(
            "admin:admin_widgets_school_change", args=(self.school.id,)
        )
        self.selenium.get(self.live_server_url + change_url)
        # Navigate away and go back to the change form page.
        self.selenium.find_element(By.LINK_TEXT, "Home").click()
        self.selenium.back()
        expected_unselected_values = [
            str(self.arthur.id),
            str(self.bob.id),
            str(self.cliff.id),
            str(self.jason.id),
            str(self.jenny.id),
            str(self.john.id),
        ]
        expected_selected_values = [str(self.lisa.id), str(self.peter.id)]
        # Everything is still in place
        self.assertSelectOptions("#id_students_from", expected_unselected_values)
        self.assertSelectOptions("#id_students_to", expected_selected_values)
        self.assertSelectOptions("#id_alumni_from", expected_unselected_values)
        self.assertSelectOptions("#id_alumni_to", expected_selected_values)