def test_inline_formset_error(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_holder5_add")
        )
        stacked_inline_details_selector = (
            "div#inner5stacked_set-group fieldset.module.collapse details"
        )
        tabular_inline_details_selector = (
            "div#inner5tabular_set-group fieldset.module.collapse details"
        )
        # Inlines without errors, both inlines collapsed
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.assertCountSeleniumElements(
            stacked_inline_details_selector + ":not([open])", 1
        )
        self.assertCountSeleniumElements(
            tabular_inline_details_selector + ":not([open])", 1
        )
        summaries = self.selenium.find_elements(By.TAG_NAME, "summary")
        self.assertEqual(len(summaries), 2)

        # Inlines with errors, both inlines expanded
        test_fields = ["#id_inner5stacked_set-0-dummy", "#id_inner5tabular_set-0-dummy"]
        for show_index, field_name in enumerate(test_fields):
            summaries[show_index].click()
            self.wait_until_visible(field_name)
            self.selenium.find_element(By.ID, field_name[1:]).send_keys(1)
        for hide_index, field_name in enumerate(test_fields):
            summary = summaries[hide_index]
            self.selenium.execute_script(
                "window.scrollTo(0, %s);" % summary.location["y"]
            )
            summary.click()
            self.wait_until_invisible(field_name)
        with self.wait_page_loaded():
            self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.assertCountSeleniumElements(stacked_inline_details_selector, 0)
        self.assertCountSeleniumElements(tabular_inline_details_selector, 0)