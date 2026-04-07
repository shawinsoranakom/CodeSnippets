def test_list_editable_popups(self):
        """
        list_editable foreign keys have add/change popups.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        s1 = Section.objects.create(name="Test section")
        Article.objects.create(
            title="foo",
            content="<p>Middle content</p>",
            date=datetime.datetime(2008, 3, 18, 11, 54, 58),
            section=s1,
        )
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_article_changelist")
        )
        # Change popup
        self.selenium.find_element(By.ID, "change_id_form-0-section").click()
        self.wait_for_and_switch_to_popup()
        self.wait_for_text("#content h1", "Change section")
        name_input = self.selenium.find_element(By.ID, "id_name")
        name_input.clear()
        name_input.send_keys("<i>edited section</i>")
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])
        # Hide sidebar.
        toggle_button = self.selenium.find_element(
            By.CSS_SELECTOR, "#toggle-nav-sidebar"
        )
        toggle_button.click()
        self.addCleanup(_clean_sidebar_state, self.selenium)
        select = Select(self.selenium.find_element(By.ID, "id_form-0-section"))
        self.assertEqual(select.first_selected_option.text, "<i>edited section</i>")
        # Rendered select2 input.
        select2_display = self.selenium.find_element(
            By.CLASS_NAME, "select2-selection__rendered"
        )
        # Clear button (×\n) is included in text.
        self.assertEqual(select2_display.text, "×\n<i>edited section</i>")

        # Add popup
        self.selenium.find_element(By.ID, "add_id_form-0-section").click()
        self.wait_for_and_switch_to_popup()
        self.wait_for_text("#content h1", "Add section")
        self.selenium.find_element(By.ID, "id_name").send_keys("new section")
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])
        select = Select(self.selenium.find_element(By.ID, "id_form-0-section"))
        self.assertEqual(select.first_selected_option.text, "new section")
        select2_display = self.selenium.find_element(
            By.CLASS_NAME, "select2-selection__rendered"
        )
        # Clear button (×\n) is included in text.
        self.assertEqual(select2_display.text, "×\nnew section")