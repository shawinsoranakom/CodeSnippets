def test_calendar_show_date_from_input(self):
        """
        The calendar shows the date from the input field for every locale
        supported by Django.
        """
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret", login_url="/")

        # Enter test data
        member = Member.objects.create(
            name="Bob", birthdate=datetime(1984, 5, 15), gender="M"
        )

        # Get month name translations for every locale
        month_string = "May"
        path = os.path.join(
            os.path.dirname(import_module("django.contrib.admin").__file__), "locale"
        )
        url = reverse("admin:admin_widgets_member_change", args=(member.pk,))
        with self.small_screen_size():
            for language_code, language_name in settings.LANGUAGES:
                try:
                    catalog = gettext.translation("djangojs", path, [language_code])
                except OSError:
                    continue
                if month_string in catalog._catalog:
                    month_name = catalog._catalog[month_string]
                else:
                    month_name = month_string

                # Get the expected caption.
                may_translation = month_name
                expected_caption = "{:s} {:d}".format(may_translation.upper(), 1984)

                # Every locale.
                with override_settings(LANGUAGE_CODE=language_code):
                    # Open a page that has a date picker widget.
                    self.selenium.get(self.live_server_url + url)
                    # Click on the calendar icon.
                    self.selenium.find_element(By.ID, "calendarlink0").click()
                    # The right month and year are displayed.
                    self.wait_for_text("#calendarin0 caption", expected_caption)