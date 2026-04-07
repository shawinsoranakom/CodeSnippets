def test_save_without_changes_warns_on_pending_action(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        Parent.objects.create(name="parent")

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_changelist_parent_changelist")
        )

        Select(self.selenium.find_element(By.NAME, "action")).select_by_value(
            "delete_selected"
        )
        self.selenium.find_element(By.NAME, "_save").click()
        alert = self.selenium.switch_to.alert
        try:
            self.assertEqual(
                alert.text,
                "You have selected an action, and you haven’t made any "
                "changes on individual fields. You’re probably looking for "
                "the Go button rather than the Save button.",
            )
        finally:
            alert.dismiss()