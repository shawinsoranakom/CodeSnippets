def test_ForeignKey_using_to_field(self):
        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        self.admin_login(username="super", password="secret", login_url="/")
        with self.wait_page_loaded():
            self.selenium.get(
                self.live_server_url + reverse("admin:admin_widgets_profile_add")
            )

        main_window = self.selenium.current_window_handle
        # Click the Add User button to add new
        self.selenium.find_element(By.ID, "add_id_user").click()
        self.wait_for_and_switch_to_popup()
        password_field = self.selenium.find_element(By.ID, "id_password")
        password_field.send_keys("password")

        username_field = self.selenium.find_element(By.ID, "id_username")
        username_value = "newuser"
        username_field.send_keys(username_value)

        save_button_css_selector = ".submit-row > input[type=submit]"
        self.selenium.find_element(By.CSS_SELECTOR, save_button_css_selector).click()
        self.selenium.switch_to.window(main_window)
        # The field now contains the new user
        self.selenium.find_element(By.CSS_SELECTOR, "#id_user option[value=newuser]")

        self.selenium.find_element(By.ID, "view_id_user").click()
        self.wait_for_value("#id_username", "newuser")
        self.selenium.back()

        # Chrome and Safari don't update related object links when selecting
        # the same option as previously submitted. As a consequence, the
        # "pencil" and "eye" buttons remain disable, so select "---------"
        # first.
        select = Select(self.selenium.find_element(By.ID, "id_user"))
        select.select_by_index(0)
        select.select_by_value("newuser")
        # Click the Change User button to change it
        self.selenium.find_element(By.ID, "change_id_user").click()
        self.wait_for_and_switch_to_popup()

        username_field = self.selenium.find_element(By.ID, "id_username")
        username_value = "changednewuser"
        username_field.clear()
        username_field.send_keys(username_value)

        save_button_css_selector = ".submit-row > input[type=submit]"
        self.selenium.find_element(By.CSS_SELECTOR, save_button_css_selector).click()
        self.selenium.switch_to.window(main_window)
        self.selenium.find_element(
            By.CSS_SELECTOR, "#id_user option[value=changednewuser]"
        )

        element = self.selenium.find_element(By.ID, "view_id_user")
        ActionChains(self.selenium).move_to_element(element).click(element).perform()
        self.wait_for_value("#id_username", "changednewuser")
        self.selenium.back()

        select = Select(self.selenium.find_element(By.ID, "id_user"))
        select.select_by_value("changednewuser")
        # Go ahead and submit the form to make sure it works
        self.selenium.find_element(By.CSS_SELECTOR, save_button_css_selector).click()
        self.wait_for_text(
            "li.success", "The profile “changednewuser” was added successfully."
        )
        profiles = Profile.objects.all()
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].user.username, username_value)