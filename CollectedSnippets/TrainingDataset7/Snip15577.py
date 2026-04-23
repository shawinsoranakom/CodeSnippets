def test_add_inlines(self):
        """
        The "Add another XXX" link correctly adds items to the inline form.
        """
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_profilecollection_add")
        )

        # There's only one inline to start with and it has the correct ID.
        self.assertCountSeleniumElements(".dynamic-profile_set", 1)
        self.assertEqual(
            self.selenium.find_elements(By.CSS_SELECTOR, ".dynamic-profile_set")[
                0
            ].get_attribute("id"),
            "profile_set-0",
        )
        self.assertCountSeleniumElements(
            ".dynamic-profile_set#profile_set-0 input[name=profile_set-0-first_name]", 1
        )
        self.assertCountSeleniumElements(
            ".dynamic-profile_set#profile_set-0 input[name=profile_set-0-last_name]", 1
        )

        # Add an inline
        self.selenium.find_element(By.LINK_TEXT, "Add another Profile").click()

        # The inline has been added, it has the right id, and it contains the
        # correct fields.
        self.assertCountSeleniumElements(".dynamic-profile_set", 2)
        self.assertEqual(
            self.selenium.find_elements(By.CSS_SELECTOR, ".dynamic-profile_set")[
                1
            ].get_attribute("id"),
            "profile_set-1",
        )
        self.assertCountSeleniumElements(
            ".dynamic-profile_set#profile_set-1 input[name=profile_set-1-first_name]", 1
        )
        self.assertCountSeleniumElements(
            ".dynamic-profile_set#profile_set-1 input[name=profile_set-1-last_name]", 1
        )
        # Let's add another one to be sure
        self.selenium.find_element(By.LINK_TEXT, "Add another Profile").click()
        self.assertCountSeleniumElements(".dynamic-profile_set", 3)
        self.assertEqual(
            self.selenium.find_elements(By.CSS_SELECTOR, ".dynamic-profile_set")[
                2
            ].get_attribute("id"),
            "profile_set-2",
        )
        self.assertCountSeleniumElements(
            ".dynamic-profile_set#profile_set-2 input[name=profile_set-2-first_name]", 1
        )
        self.assertCountSeleniumElements(
            ".dynamic-profile_set#profile_set-2 input[name=profile_set-2-last_name]", 1
        )

        # Enter some data and click 'Save'
        self.selenium.find_element(By.NAME, "profile_set-0-first_name").send_keys(
            "0 first name 1"
        )
        self.selenium.find_element(By.NAME, "profile_set-0-last_name").send_keys(
            "0 last name 2"
        )
        self.selenium.find_element(By.NAME, "profile_set-1-first_name").send_keys(
            "1 first name 1"
        )
        self.selenium.find_element(By.NAME, "profile_set-1-last_name").send_keys(
            "1 last name 2"
        )
        self.selenium.find_element(By.NAME, "profile_set-2-first_name").send_keys(
            "2 first name 1"
        )
        self.selenium.find_element(By.NAME, "profile_set-2-last_name").send_keys(
            "2 last name 2"
        )

        with self.wait_page_loaded():
            self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()

        # The objects have been created in the database
        self.assertEqual(ProfileCollection.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 3)