def test_selectbox_height_collapsible_fieldset(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super",
            password="secret",
            login_url=reverse("admin7:index"),
        )
        url = self.live_server_url + reverse("admin7:admin_views_pizza_add")
        self.selenium.get(url)
        self.selenium.find_elements(By.TAG_NAME, "summary")[0].click()
        from_filter_box = self.selenium.find_element(By.ID, "id_toppings_filter")
        from_box = self.selenium.find_element(By.ID, "id_toppings_from")
        to_filter_box = self.selenium.find_element(By.ID, "id_toppings_filter_selected")
        to_box = self.selenium.find_element(By.ID, "id_toppings_to")
        self.assertEqual(
            (
                to_filter_box.get_property("offsetHeight")
                + to_box.get_property("offsetHeight")
            ),
            (
                from_filter_box.get_property("offsetHeight")
                + from_box.get_property("offsetHeight")
            ),
        )
        self.take_screenshot("selectbox-collapsible")