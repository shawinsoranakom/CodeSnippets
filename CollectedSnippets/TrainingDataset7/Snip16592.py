def test_use_fieldset_with_grouped_fields(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_course_add")
        )
        multiline = self.selenium.find_element(
            By.CSS_SELECTOR, "#content-main .field-difficulty, .form-multiline"
        )
        # Two field boxes.
        field_boxes = multiline.find_elements(By.XPATH, "./*")
        self.assertEqual(len(field_boxes), 2)
        # One of them is under a <fieldset>.
        under_fieldset = multiline.find_elements(By.TAG_NAME, "fieldset")
        self.assertEqual(len(under_fieldset), 1)
        self.take_screenshot("horizontal_fieldset")