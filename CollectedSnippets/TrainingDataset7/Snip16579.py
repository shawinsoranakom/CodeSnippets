def test_inline_uuid_pk_add_with_popup(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url
            + reverse("admin:admin_views_relatedwithuuidpkmodel_add")
        )
        self.selenium.find_element(By.ID, "add_id_parent").click()
        self.wait_for_and_switch_to_popup()
        self.selenium.find_element(By.ID, "id_title").send_keys("test")
        self.selenium.find_element(By.XPATH, '//input[@value="Save"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])
        select = Select(self.selenium.find_element(By.ID, "id_parent"))
        uuid_id = str(ParentWithUUIDPK.objects.first().id)
        self.assertEqual(select.first_selected_option.text, uuid_id)
        self.assertEqual(select.first_selected_option.get_attribute("value"), uuid_id)