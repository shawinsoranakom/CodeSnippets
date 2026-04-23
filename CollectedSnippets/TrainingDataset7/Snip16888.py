def test_ForeignKey(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret", login_url="/")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_widgets_event_add")
        )
        main_window = self.selenium.current_window_handle
        self.take_screenshot("raw_id_widget")

        # No value has been selected yet
        self.assertEqual(
            self.selenium.find_element(By.ID, "id_main_band").get_attribute("value"), ""
        )

        # Open the popup window and click on a band
        self.selenium.find_element(By.ID, "lookup_id_main_band").click()
        self.wait_for_and_switch_to_popup()
        link = self.selenium.find_element(By.LINK_TEXT, "Bogey Blues")
        self.assertIn(f"/band/{self.blues.pk}/", link.get_attribute("href"))
        link.click()

        # The field now contains the selected band's id
        self.selenium.switch_to.window(main_window)
        self.wait_for_value("#id_main_band", str(self.blues.pk))

        # Reopen the popup window and click on another band
        self.selenium.find_element(By.ID, "lookup_id_main_band").click()
        self.wait_for_and_switch_to_popup()
        link = self.selenium.find_element(By.LINK_TEXT, "Green Potatoes")
        self.assertIn(f"/band/{self.potatoes.pk}/", link.get_attribute("href"))
        link.click()

        # The field now contains the other selected band's id
        self.selenium.switch_to.window(main_window)
        self.wait_for_value("#id_main_band", str(self.potatoes.pk))