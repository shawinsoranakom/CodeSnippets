def test_selectbox_selected_rows(self):
        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        # Create a new user to ensure that no extra permissions have been set.
        user = User.objects.create_user(username="new", password="newuser")
        url = self.live_server_url + reverse("admin:auth_user_change", args=[user.id])
        self.selenium.get(url)
        self.trigger_resize()

        # Scroll to the User permissions section.
        user_permissions = self.selenium.find_element(
            By.CSS_SELECTOR, "#id_user_permissions_from"
        )
        ActionChains(self.selenium).move_to_element(user_permissions).perform()
        self.take_screenshot("selectbox-available-perms-none-selected")

        # Select multiple permissions from the "Available" list.
        ct = ContentType.objects.get_for_model(Permission)
        perms = list(Permission.objects.filter(content_type=ct))
        for perm in perms:
            elem = self.selenium.find_element(
                By.CSS_SELECTOR, f"#id_user_permissions_from option[value='{perm.id}']"
            )
            ActionChains(self.selenium).key_down(self.modifier_key).click(elem).key_up(
                self.modifier_key
            ).perform()

        # Move focus to other element.
        self.selenium.find_element(
            By.CSS_SELECTOR, "#id_user_permissions_input"
        ).click()
        self.take_screenshot("selectbox-available-perms-some-selected")

        # Move permissions to the "Chosen" list, but none is selected yet.
        self.selenium.find_element(By.CSS_SELECTOR, "#id_user_permissions_add").click()
        self.take_screenshot("selectbox-chosen-perms-none-selected")

        # Select some permissions from the "Chosen" list.
        for perm in [perms[0], perms[-1]]:
            elem = self.selenium.find_element(
                By.CSS_SELECTOR, f"#id_user_permissions_to option[value='{perm.id}']"
            )
            ActionChains(self.selenium).key_down(self.modifier_key).click(elem).key_up(
                self.modifier_key
            ).perform()

        # Move focus to other element.
        body = self.selenium.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.TAB)
        self.take_screenshot("selectbox-chosen-perms-some-selected")