def test_added_stacked_inline_with_collapsed_fields(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_teacher_add")
        )
        add_text = gettext("Add another %(verbose_name)s") % {"verbose_name": "Child"}
        self.selenium.find_element(By.LINK_TEXT, add_text).click()
        test_fields = ["#id_child_set-0-name", "#id_child_set-1-name"]
        summaries = self.selenium.find_elements(By.TAG_NAME, "summary")
        self.assertEqual(len(summaries), 3)
        self.take_screenshot("loaded")
        for show_index, field_name in enumerate(test_fields, 0):
            self.wait_until_invisible(field_name)
            summaries[show_index].click()
            self.wait_until_visible(field_name)
        self.take_screenshot("expanded")
        for hide_index, field_name in enumerate(test_fields, 0):
            self.wait_until_visible(field_name)
            summaries[hide_index].click()
            self.wait_until_invisible(field_name)
        self.take_screenshot("collapsed")