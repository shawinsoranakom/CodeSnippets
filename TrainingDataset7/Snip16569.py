def test_populate_existing_object(self):
        """
        The prepopulation works for existing objects too, as long as
        the original field is empty (#19082).
        """
        from selenium.webdriver.common.by import By

        # Slugs are empty to start with.
        item = MainPrepopulated.objects.create(
            name=" this is the mAin nÀMë",
            pubdate="2012-02-18",
            status="option two",
            slug1="",
            slug2="",
        )
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )

        object_url = self.live_server_url + reverse(
            "admin:admin_views_mainprepopulated_change", args=(item.id,)
        )

        self.selenium.get(object_url)
        self.selenium.find_element(By.ID, "id_name").send_keys(" the best")

        # The slugs got prepopulated since they were originally empty
        slug1 = self.selenium.find_element(By.ID, "id_slug1").get_attribute("value")
        slug2 = self.selenium.find_element(By.ID, "id_slug2").get_attribute("value")
        self.assertEqual(slug1, "this-is-the-main-name-the-best-2012-02-18")
        self.assertEqual(slug2, "option-two-this-is-the-main-name-the-best")

        # Save the object
        with self.wait_page_loaded():
            self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()

        self.selenium.get(object_url)
        self.selenium.find_element(By.ID, "id_name").send_keys(" hello")

        # The slugs got prepopulated didn't change since they were originally
        # not empty
        slug1 = self.selenium.find_element(By.ID, "id_slug1").get_attribute("value")
        slug2 = self.selenium.find_element(By.ID, "id_slug2").get_attribute("value")
        self.assertEqual(slug1, "this-is-the-main-name-the-best-2012-02-18")
        self.assertEqual(slug2, "option-two-this-is-the-main-name-the-best")