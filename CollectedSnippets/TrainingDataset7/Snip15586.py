def test_tabular_inline_layout(self):
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_photographer_add")
        )
        tabular_inline = self.selenium.find_element(
            By.CSS_SELECTOR, "[data-inline-type='tabular']"
        )
        headers = tabular_inline.find_elements(By.TAG_NAME, "th")
        self.assertEqual(
            [h.get_attribute("innerText") for h in headers],
            [
                "",
                "IMAGE",
                "TITLE",
                "DESCRIPTION",
                "CREATION DATE",
                "UPDATE DATE",
                "UPDATED BY",
                "DELETE?",
            ],
        )
        # There are no fieldset section names rendered.
        self.assertNotIn("Details", tabular_inline.text)
        # There are no fieldset section descriptions rendered.
        self.assertNotIn("First group", tabular_inline.text)
        self.assertNotIn("Second group", tabular_inline.text)
        self.assertNotIn("Third group", tabular_inline.text)
        # There are no fieldset classes applied.
        self.assertEqual(
            tabular_inline.find_elements(By.CSS_SELECTOR, ".collapse"),
            [],
        )
        # The table does not overflow the content section.
        content = self.selenium.find_element(By.ID, "content-main")
        tabular_wrapper = self.selenium.find_element(
            By.CSS_SELECTOR, "div.tabular.inline-related div.wrapper"
        )
        self.assertGreater(
            tabular_wrapper.find_element(By.TAG_NAME, "table").size["width"],
            tabular_wrapper.size["width"],
        )
        self.assertLessEqual(tabular_wrapper.size["width"], content.size["width"])