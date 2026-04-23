def test_date_time_picker_shortcuts(self):
        """
        date/time/datetime picker shortcuts work in the current time zone.
        Refs #20663.

        This test case is fairly tricky, it relies on selenium still running
        the browser in the default time zone "America/Chicago" despite
        `override_settings` changing the time zone to "Asia/Singapore".
        """
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret", login_url="/")

        error_margin = timedelta(seconds=10)

        # If we are neighbouring a DST, we add an hour of error margin.
        tz = zoneinfo.ZoneInfo("America/Chicago")
        utc_now = datetime.now(zoneinfo.ZoneInfo("UTC"))
        tz_yesterday = (utc_now - timedelta(days=1)).astimezone(tz).tzname()
        tz_tomorrow = (utc_now + timedelta(days=1)).astimezone(tz).tzname()
        if tz_yesterday != tz_tomorrow:
            error_margin += timedelta(hours=1)

        self.selenium.get(
            self.live_server_url + reverse("admin:admin_widgets_member_add")
        )

        self.selenium.find_element(By.ID, "id_name").send_keys("test")

        # Click on the "today" and "now" shortcuts.
        shortcuts = self.selenium.find_elements(
            By.CSS_SELECTOR, ".field-birthdate .datetimeshortcuts"
        )

        now = datetime.now()
        for shortcut in shortcuts:
            shortcut.find_element(By.TAG_NAME, "a").click()

        # There is a time zone mismatch warning.
        # Warning: This would effectively fail if the TIME_ZONE defined in the
        # settings has the same UTC offset as "Asia/Singapore" because the
        # mismatch warning would be rightfully missing from the page.
        self.assertCountSeleniumElements(".field-birthdate .timezonewarning", 1)

        # Submit the form.
        with self.wait_page_loaded():
            self.selenium.find_element(By.NAME, "_save").click()

        # Make sure that "now" in JavaScript is within 10 seconds
        # from "now" on the server side.
        member = Member.objects.get(name="test")
        self.assertGreater(member.birthdate, now - error_margin)
        self.assertLess(member.birthdate, now + error_margin)