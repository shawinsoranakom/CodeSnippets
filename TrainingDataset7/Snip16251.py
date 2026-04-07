def test_use_skip_link_to_content(self):
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        self.admin_login(
            username="super",
            password="secret",
            login_url=reverse("admin:index"),
        )

        # `Skip link` is not present.
        skip_link = self.selenium.find_element(By.CLASS_NAME, "skip-to-content-link")
        self.assertFalse(skip_link.is_displayed())

        # 1st TAB is pressed, `skip link` is shown.
        body = self.selenium.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.TAB)
        self.assertTrue(skip_link.is_displayed())

        # Press RETURN to skip the navbar links (view site / documentation /
        # change password / log out) and focus first model in the admin_views
        # list.
        skip_link.send_keys(Keys.RETURN)
        self.assertFalse(skip_link.is_displayed())  # `skip link` disappear.
        keys = [Keys.TAB, Keys.TAB]  # The 1st TAB is the section title.
        if self.browser == "firefox":
            # For some reason Firefox doesn't focus the section title
            # ('ADMIN_VIEWS').
            keys.remove(Keys.TAB)
        body.send_keys(keys)
        actors_a_tag = self.selenium.find_element(By.LINK_TEXT, "Actors")
        self.assertEqual(self.selenium.switch_to.active_element, actors_a_tag)

        # Go to Actors changelist, skip sidebar and focus "Add actor +".
        with self.wait_page_loaded():
            actors_a_tag.send_keys(Keys.RETURN)
        body = self.selenium.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.TAB)
        skip_link = self.selenium.find_element(By.CLASS_NAME, "skip-to-content-link")
        self.assertTrue(skip_link.is_displayed())
        ActionChains(self.selenium).send_keys(Keys.RETURN, Keys.TAB).perform()
        actors_add_url = reverse("admin:admin_views_actor_add")
        actors_a_tag = self.selenium.find_element(
            By.CSS_SELECTOR, f"#content [href='{actors_add_url}']"
        )
        self.assertEqual(self.selenium.switch_to.active_element, actors_a_tag)

        # Go to the Actor form and the first input will be focused
        # automatically.
        with self.wait_page_loaded():
            actors_a_tag.send_keys(Keys.RETURN)
        first_input = self.selenium.find_element(By.ID, "id_name")
        self.assertEqual(self.selenium.switch_to.active_element, first_input)