def test_modifier_allows_multiple_section(self):
        """
        Selecting a row and then selecting another row whilst holding shift
        should select all rows in-between.
        """
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        Parent.objects.bulk_create([Parent(name="parent%d" % i) for i in range(5)])
        self.admin_login(username="super", password="secret")
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_changelist_parent_changelist")
        )
        checkboxes = self.selenium.find_elements(
            By.CSS_SELECTOR, "tr input.action-select"
        )
        self.assertEqual(len(checkboxes), 5)
        for c in checkboxes:
            self.assertIs(c.get_property("checked"), False)
        # Check first row. Hold-shift and check next-to-last row.
        checkboxes[0].click()
        ActionChains(self.selenium).key_down(Keys.SHIFT).click(checkboxes[-2]).key_up(
            Keys.SHIFT
        ).perform()
        for c in checkboxes[:-2]:
            self.assertIs(c.get_property("checked"), True)
        self.assertIs(checkboxes[-1].get_property("checked"), False)