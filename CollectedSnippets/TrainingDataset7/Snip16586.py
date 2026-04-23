def test_related_popup_incorrect_close(self):
        """
        Cleanup child popups when closing a parent popup.
        """
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        add_url = reverse("admin:admin_views_box_add", current_app=site.name)
        self.selenium.get(self.live_server_url + add_url)

        self.selenium.find_element(By.ID, "add_id_next_box").click()
        self.wait_for_and_switch_to_popup()

        test_window = self.selenium.current_window_handle
        self.selenium.find_element(By.ID, "id_title").send_keys("test")
        self.selenium.find_element(By.ID, "add_id_next_box").click()
        self.wait_for_and_switch_to_popup(num_windows=3)

        test2_window = self.selenium.current_window_handle
        self.selenium.find_element(By.ID, "id_title").send_keys("test2")
        self.selenium.find_element(By.ID, "add_id_next_box").click()
        self.wait_for_and_switch_to_popup(num_windows=4)
        self.assertEqual(len(self.selenium.window_handles), 4)

        self.selenium.switch_to.window(test2_window)
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 2, 1)
        self.assertEqual(len(self.selenium.window_handles), 2)

        # Close final popup to clean up test.
        self.selenium.switch_to.window(test_window)
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[-1])