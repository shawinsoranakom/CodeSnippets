def test_inlines_verbose_name(self):
        """
        The item added by the "Add another XXX" link must use the correct
        verbose_name in the inline form.
        """
        from selenium.webdriver.common.by import By

        self.admin_login(username="super", password="secret")
        # Hide sidebar.
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_inlines_course_add")
        )
        toggle_button = self.selenium.find_element(
            By.CSS_SELECTOR, "#toggle-nav-sidebar"
        )
        toggle_button.click()
        # Each combination of horizontal/vertical filter with stacked/tabular
        # inlines.
        tests = [
            "admin:admin_inlines_course_add",
            "admin:admin_inlines_courseproxy_add",
            "admin:admin_inlines_courseproxy1_add",
            "admin:admin_inlines_courseproxy2_add",
        ]
        css_available_selector = (
            ".dynamic-class_set#class_set-%s .selector-available-title"
        )
        css_chosen_selector = ".dynamic-class_set#class_set-%s .selector-chosen-title"

        for url_name in tests:
            with self.subTest(url=url_name):
                self.selenium.get(self.live_server_url + reverse(url_name))
                # First inline shows the verbose_name.
                available = self.selenium.find_element(
                    By.CSS_SELECTOR, css_available_selector % 0
                )
                chosen = self.selenium.find_element(
                    By.CSS_SELECTOR, css_chosen_selector % 0
                )
                self.assertIn("Available attendant", available.text)
                self.assertIn("Chosen attendant", chosen.text)
                # Added inline should also have the correct verbose_name.
                self.selenium.find_element(By.LINK_TEXT, "Add another Class").click()
                available = self.selenium.find_element(
                    By.CSS_SELECTOR, css_available_selector % 1
                )
                chosen = self.selenium.find_element(
                    By.CSS_SELECTOR, css_chosen_selector % 1
                )
                self.assertIn("Available attendant", available.text)
                self.assertIn("Chosen attendant", chosen.text)
                # Third inline should also have the correct verbose_name.
                self.selenium.find_element(By.LINK_TEXT, "Add another Class").click()
                available = self.selenium.find_element(
                    By.CSS_SELECTOR, css_available_selector % 2
                )
                chosen = self.selenium.find_element(
                    By.CSS_SELECTOR, css_chosen_selector % 2
                )
                self.assertIn("Available attendant", available.text)
                self.assertIn("Chosen attendant", chosen.text)