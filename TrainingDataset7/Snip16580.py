def test_inline_uuid_pk_delete_with_popup(self):
        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        parent = ParentWithUUIDPK.objects.create(title="test")
        related_with_parent = RelatedWithUUIDPKModel.objects.create(parent=parent)
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        change_url = reverse(
            "admin:admin_views_relatedwithuuidpkmodel_change",
            args=(related_with_parent.id,),
        )
        with self.wait_page_loaded():
            self.selenium.get(self.live_server_url + change_url)
        delete_parent = self.selenium.find_element(By.ID, "delete_id_parent")
        ActionChains(self.selenium).move_to_element(delete_parent).click().perform()
        self.wait_for_and_switch_to_popup()
        self.selenium.find_element(By.XPATH, '//input[@value="Yes, I’m sure"]').click()
        self.wait_until(lambda d: len(d.window_handles) == 1, 1)
        self.selenium.switch_to.window(self.selenium.window_handles[0])
        select = Select(self.selenium.find_element(By.ID, "id_parent"))
        self.assertEqual(ParentWithUUIDPK.objects.count(), 0)
        self.assertEqual(select.first_selected_option.text, "---------")
        self.assertEqual(select.first_selected_option.get_attribute("value"), "")