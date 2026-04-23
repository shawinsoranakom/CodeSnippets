def test_first_field_focus(self):
        """JavaScript-assisted auto-focus on first usable form field."""
        from selenium.webdriver.common.by import By

        # First form field has a single widget
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        with self.wait_page_loaded():
            self.selenium.get(
                self.live_server_url + reverse("admin:admin_views_picture_add")
            )
        self.assertEqual(
            self.selenium.switch_to.active_element,
            self.selenium.find_element(By.ID, "id_name"),
        )
        self.take_screenshot("focus-single-widget")

        # First form field has a MultiWidget
        with self.wait_page_loaded():
            self.selenium.get(
                self.live_server_url + reverse("admin:admin_views_reservation_add")
            )
        self.assertEqual(
            self.selenium.switch_to.active_element,
            self.selenium.find_element(By.ID, "id_start_date_0"),
        )
        self.take_screenshot("focus-multi-widget")