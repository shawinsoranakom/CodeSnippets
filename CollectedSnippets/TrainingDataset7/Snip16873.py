def test_calendar_nonday_class(self):
        """
        Ensure cells that are not days of the month have the `nonday` CSS
        class. Refs #4574.
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

        # make sure the first and last 6 cells have class nonday
        for td in tds[:6] + tds[-6:]:
            self.assertEqual(td.get_attribute("class"), "nonday")