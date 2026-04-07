def test_form_submission_via_enter_key_with_filter_horizontal(self):
        """
        The main form can be submitted correctly by pressing the enter key.
        There is no shadowing from other buttons inside the form.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        self.school.students.set([self.peter])
        self.school.alumni.set([self.lisa])

        self.admin_login(username="super", password="secret", login_url="/")
        self.selenium.get(
            self.live_server_url
            + reverse("admin:admin_widgets_school_change", args=(self.school.id,))
        )

        self.wait_page_ready()
        self.select_option("#id_students_from", str(self.lisa.id))
        self.selenium.find_element(By.ID, "id_students_add").click()
        self.select_option("#id_alumni_from", str(self.peter.id))
        self.selenium.find_element(By.ID, "id_alumni_add").click()

        # Trigger form submission via Enter key on a text input field.
        name_input = self.selenium.find_element(By.ID, "id_name")
        name_input.click()
        name_input.send_keys(Keys.ENTER)

        # Form was submitted, success message should be shown.
        self.wait_for_text(
            "li.success", "The school “School of Awesome” was changed successfully."
        )

        # Changes should be stored properly in the database.
        school = School.objects.get(id=self.school.id)
        self.assertSequenceEqual(
            school.students.all().order_by("name"), [self.lisa, self.peter]
        )
        self.assertSequenceEqual(
            school.alumni.all().order_by("name"), [self.lisa, self.peter]
        )