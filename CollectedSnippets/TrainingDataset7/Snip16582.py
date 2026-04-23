def test_list_editable_raw_id_fields(self):
        from selenium.webdriver.common.by import By

        parent = ParentWithUUIDPK.objects.create(title="test")
        parent2 = ParentWithUUIDPK.objects.create(title="test2")
        RelatedWithUUIDPKModel.objects.create(parent=parent)
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        change_url = reverse(
            "admin:admin_views_relatedwithuuidpkmodel_changelist",
            current_app=site2.name,
        )
        self.selenium.get(self.live_server_url + change_url)
        self.selenium.find_element(By.ID, "lookup_id_form-0-parent").click()
        self.wait_for_and_switch_to_popup()
        # Select "parent2" in the popup.
        self.selenium.find_element(By.LINK_TEXT, str(parent2.pk)).click()
        self.selenium.switch_to.window(self.selenium.window_handles[0])
        # The newly selected pk should appear in the raw id input.
        value = self.selenium.find_element(By.ID, "id_form-0-parent").get_attribute(
            "value"
        )
        self.assertEqual(value, str(parent2.pk))