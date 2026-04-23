def test_calendar_no_selected_class(self):
        """
        Ensure no cells are given the selected class when the field is empty.
        Refs #4574.
        """
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret", login_url="/")
        # Open a page that has a date and time picker widgets
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_widgets_member_add")
        )

        # Click the calendar icon
        self.selenium.find_element(By.ID, "calendarlink0").click()

        # get all the tds within the calendar
        calendar0 = self.selenium.find_element(By.ID, "calendarin0")
        tds = calendar0.find_elements(By.TAG_NAME, "td")

        # verify there are no cells with the selected class
        selected = [td for td in tds if td.get_attribute("class") == "selected"]

        self.assertEqual(len(selected), 0)