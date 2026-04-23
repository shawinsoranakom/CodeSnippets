def test_redirect_on_add_view_continue_button(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        add_url = reverse("admin7:admin_views_section_add")
        self.selenium.get(self.live_server_url + add_url)
        name_input = self.selenium.find_element(By.ID, "id_name")
        name_input.send_keys("Test section 1")
        with self.wait_page_loaded():
            self.selenium.find_element(
                By.XPATH, '//input[@value="Save and continue editing"]'
            ).click()
        self.assertEqual(Section.objects.count(), 1)
        name_input = self.selenium.find_element(By.ID, "id_name")
        name_input_value = name_input.get_attribute("value")
        self.assertEqual(name_input_value, "Test section 1")