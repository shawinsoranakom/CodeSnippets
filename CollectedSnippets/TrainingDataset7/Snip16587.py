def test_hidden_fields_small_window(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super",
            password="secret",
            login_url=reverse("admin:index"),
        )
        self.selenium.get(self.live_server_url + reverse("admin:admin_views_story_add"))
        field_title = self.selenium.find_element(By.CLASS_NAME, "field-title")
        with self.small_screen_size():
            self.assertIs(field_title.is_displayed(), False)
        with self.mobile_size():
            self.assertIs(field_title.is_displayed(), False)