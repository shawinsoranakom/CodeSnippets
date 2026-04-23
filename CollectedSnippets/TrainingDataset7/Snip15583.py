def test_inline_formset_error_input_border(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_holder5_add")
        )
        self.wait_until_visible("#id_dummy")
        self.selenium.find_element(By.ID, "id_dummy").send_keys(1)
        fields = ["id_inner5stacked_set-0-dummy", "id_inner5tabular_set-0-dummy"]
        summaries = self.selenium.find_elements(By.TAG_NAME, "summary")
        for show_index, field_name in enumerate(fields):
            summaries[show_index].click()
            self.wait_until_visible("#" + field_name)
            self.selenium.find_element(By.ID, field_name).send_keys(1)

        # Before save all inputs have default border
        for inline in ("stacked", "tabular"):
            for field_name in ("name", "select", "text"):
                element_id = "id_inner5%s_set-0-%s" % (inline, field_name)
                self.assertBorder(
                    self.selenium.find_element(By.ID, element_id),
                    "1px solid #cccccc",
                )
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        # Test the red border around inputs by css selectors
        stacked_selectors = [".errors input", ".errors select", ".errors textarea"]
        for selector in stacked_selectors:
            self.assertBorder(
                self.selenium.find_element(By.CSS_SELECTOR, selector),
                "1px solid #ba2121",
            )
        tabular_selectors = [
            "td ul.errorlist + input",
            "td ul.errorlist + select",
            "td ul.errorlist + textarea",
        ]
        for selector in tabular_selectors:
            self.assertBorder(
                self.selenium.find_element(By.CSS_SELECTOR, selector),
                "1px solid #ba2121",
            )