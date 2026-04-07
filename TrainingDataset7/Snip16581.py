def test_inline_with_popup_cancel_delete(self):
        """Clicking ""No, take me back" on a delete popup closes the window."""
        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.by import By

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
        self.selenium.find_element(By.XPATH, '//a[text()="No, take me back"]').click()
        self.selenium.switch_to.window(self.selenium.window_handles[0])
        self.assertEqual(len(self.selenium.window_handles), 1)