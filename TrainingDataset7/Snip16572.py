def test_selectbox_height_not_collapsible_fieldset(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super",
            password="secret",
            login_url=reverse("admin7:index"),
        )
        url = self.live_server_url + reverse("admin7:admin_views_question_add")
        self.selenium.get(url)
        from_filter_box = self.selenium.find_element(
            By.ID, "id_related_questions_filter"
        )
        from_box = self.selenium.find_element(By.ID, "id_related_questions_from")
        to_filter_box = self.selenium.find_element(
            By.ID, "id_related_questions_filter_selected"
        )
        to_box = self.selenium.find_element(By.ID, "id_related_questions_to")
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
        self.take_screenshot("selectbox-non-collapsible")