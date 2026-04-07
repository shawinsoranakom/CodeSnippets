def test_collapsed_inlines(self):
        from selenium.webdriver.common.by import By

        # Collapsed inlines use details and summary elements.
        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_author_add")
        )
        # One field is in a stacked inline, other in a tabular one.
        test_fields = [
            "#id_nonautopkbook_set-0-title",
            "#id_nonautopkbook_set-2-0-title",
        ]
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