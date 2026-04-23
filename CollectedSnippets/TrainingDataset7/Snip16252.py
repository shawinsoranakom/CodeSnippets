def test_dont_use_skip_link_to_content(self):
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

        # The 2nd TAB will focus the page title.
        body.send_keys(Keys.TAB)
        django_administration_title = self.selenium.find_element(
            By.LINK_TEXT, "Django administration"
        )
        self.assertFalse(skip_link.is_displayed())  # `skip link` disappear.
        self.assertEqual(
            self.selenium.switch_to.active_element, django_administration_title
        )