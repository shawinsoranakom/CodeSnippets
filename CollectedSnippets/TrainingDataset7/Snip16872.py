def test_show_hide_date_time_picker_widgets(self):
        """
        Pressing the ESC key or clicking on a widget value closes the date and
        time picker widgets.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        self.admin_login(username="super", password="secret", login_url="/")
        # Open a page that has a date and time picker widgets
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_widgets_member_add")
        )

        # First, with the date picker widget ---------------------------------
        cal_icon = self.selenium.find_element(By.ID, "calendarlink0")
        # The date picker is hidden
        self.assertFalse(
            self.selenium.find_element(By.ID, "calendarbox0").is_displayed()
        )
        # Click the calendar icon
        cal_icon.click()
        # The date picker is visible
        self.assertTrue(
            self.selenium.find_element(By.ID, "calendarbox0").is_displayed()
        )
        # Press the ESC key
        self.selenium.find_element(By.TAG_NAME, "body").send_keys([Keys.ESCAPE])
        # The date picker is hidden again
        self.assertFalse(
            self.selenium.find_element(By.ID, "calendarbox0").is_displayed()
        )
        # Click the calendar icon, then on the 15th of current month
        cal_icon.click()
        self.selenium.find_element(By.XPATH, "//a[contains(text(), '15')]").click()
        self.assertFalse(
            self.selenium.find_element(By.ID, "calendarbox0").is_displayed()
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, "id_birthdate_0").get_attribute("value"),
            datetime.today().strftime("%Y-%m-") + "15",
        )

        # Then, with the time picker widget ----------------------------------
        time_icon = self.selenium.find_element(By.ID, "clocklink0")
        # The time picker is hidden
        self.assertFalse(self.selenium.find_element(By.ID, "clockbox0").is_displayed())
        # Click the time icon
        time_icon.click()
        # The time picker is visible
        self.assertTrue(self.selenium.find_element(By.ID, "clockbox0").is_displayed())
        self.assertEqual(
            [
                x.text
                for x in self.selenium.find_elements(
                    By.XPATH, "//ul[@class='timelist']/li/a"
                )
            ],
            ["Now", "Midnight", "6 a.m.", "Noon", "6 p.m."],
        )
        # Press the ESC key
        self.selenium.find_element(By.TAG_NAME, "body").send_keys([Keys.ESCAPE])
        # The time picker is hidden again
        self.assertFalse(self.selenium.find_element(By.ID, "clockbox0").is_displayed())
        # Click the time icon, then select the 'Noon' value
        time_icon.click()
        self.selenium.find_element(By.XPATH, "//a[contains(text(), 'Noon')]").click()
        self.assertFalse(self.selenium.find_element(By.ID, "clockbox0").is_displayed())
        self.assertEqual(
            self.selenium.find_element(By.ID, "id_birthdate_1").get_attribute("value"),
            "12:00:00",
        )