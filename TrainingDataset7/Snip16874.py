def test_calendar_selected_class(self):
        """
        Ensure cell for the day in the input has the `selected` CSS class.
        Refs #4574.
        """
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret", login_url="/")
        # Open a page that has a date and time picker widgets
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_widgets_member_add")
        )

        # fill in the birth date.
        self.selenium.find_element(By.ID, "id_birthdate_0").send_keys("2013-06-01")

        # Click the calendar icon
        self.selenium.find_element(By.ID, "calendarlink0").click()

        # get all the tds within the calendar
        calendar0 = self.selenium.find_element(By.ID, "calendarin0")
        tds = calendar0.find_elements(By.TAG_NAME, "td")

        # verify the selected cell
        selected = tds[6]
        self.assertEqual(selected.get_attribute("class"), "selected")

        self.assertEqual(selected.text, "1")