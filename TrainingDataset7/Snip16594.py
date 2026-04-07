def test_list_editable_with_filter(self):
        from selenium.webdriver.common.by import By

        Person.objects.create(name="Tom", gender=1)
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_person_changelist")
        )
        save_button = self.selenium.find_element(By.NAME, "_save")
        self.assertTrue(save_button.is_displayed())
        self.take_screenshot("list_editable")

        with self.wait_page_loaded():
            save_button.click()