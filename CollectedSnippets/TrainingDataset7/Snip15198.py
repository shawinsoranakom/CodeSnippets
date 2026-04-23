def test_save_with_changes_warns_on_pending_action(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        Parent.objects.create(name="parent")

        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_changelist_parent_changelist")
        )

        name_input = self.selenium.find_element(By.ID, "id_form-0-name")
        name_input.clear()
        name_input.send_keys("other name")
        Select(self.selenium.find_element(By.NAME, "action")).select_by_value(
            "delete_selected"
        )
        self.selenium.find_element(By.NAME, "_save").click()
        alert = self.selenium.switch_to.alert
        try:
            self.assertEqual(
                alert.text,
                "You have selected an action, but you haven’t saved your "
                "changes to individual fields yet. Please click OK to save. "
                "You’ll need to re-run the action.",
            )
        finally:
            alert.dismiss()