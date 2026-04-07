def test_actions_warn_on_pending_edits(self):
        from selenium.webdriver.common.by import By

        Parent.objects.create(name="foo")

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_changelist_parent_changelist")
        )

        name_input = self.selenium.find_element(By.ID, "id_form-0-name")
        name_input.clear()
        name_input.send_keys("bar")
        self.selenium.find_element(By.ID, "action-toggle").click()
        self.selenium.find_element(By.NAME, "index").click()  # Go
        alert = self.selenium.switch_to.alert
        try:
            self.assertEqual(
                alert.text,
                "You have unsaved changes on individual editable fields. If you "
                "run an action, your unsaved changes will be lost.",
            )
        finally:
            alert.dismiss()