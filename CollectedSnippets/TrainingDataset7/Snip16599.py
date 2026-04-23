def test_form_errors_render_layout(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_language_add")
        )

        with self.wait_page_loaded():
            self.selenium.find_element(By.NAME, "_save").click()

        form_rows = self.selenium.find_elements(By.CSS_SELECTOR, "div.form-row")
        for row in form_rows:
            error_list = row.find_element(By.CSS_SELECTOR, "ul.errorlist")
            self.assertTrue(error_list.is_displayed())
        self.take_screenshot("error_list")