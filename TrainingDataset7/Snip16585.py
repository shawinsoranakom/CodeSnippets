def test_related_popup_index(self):
        """
        Create a chain of 'self' related objects via popups.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        add_url = reverse("admin:admin_views_box_add", current_app=site.name)
        self.selenium.get(self.live_server_url + add_url)

        base_window = self.selenium.current_window_handle
        self.selenium.find_element(By.ID, "add_id_next_box").click()
        self.wait_for_and_switch_to_popup()

        popup_window_test = self.selenium.current_window_handle
        self.selenium.find_element(By.ID, "id_title").send_keys("test")
        self.selenium.find_element(By.ID, "add_id_next_box").click()
        self.wait_for_and_switch_to_popup(num_windows=3)

        popup_window_test2 = self.selenium.current_window_handle
        self.selenium.find_element(By.ID, "id_title").send_keys("test2")
        self.selenium.find_element(By.ID, "add_id_next_box").click()
        self.wait_for_and_switch_to_popup(num_windows=4)

        self.selenium.find_element(By.ID, "id_title").send_keys("test3")
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 3, 1)
        self.selenium.switch_to.window(popup_window_test2)
        select = Select(self.selenium.find_element(By.ID, "id_next_box"))
        next_box_id = str(Box.objects.get(title="test3").id)
        self.assertEqual(
            select.first_selected_option.get_attribute("value"), next_box_id
        )

        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 2, 1)
        self.selenium.switch_to.window(popup_window_test)
        select = Select(self.selenium.find_element(By.ID, "id_next_box"))
        next_box_id = str(Box.objects.get(title="test2").id)
        self.assertEqual(
            select.first_selected_option.get_attribute("value"), next_box_id
        )

        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(base_window)
        select = Select(self.selenium.find_element(By.ID, "id_next_box"))
        next_box_id = str(Box.objects.get(title="test").id)
        self.assertEqual(
            select.first_selected_option.get_attribute("value"), next_box_id
        )